"""Dataset indexing, de-duplication, leakage-free splitting and checking.

Usage (from repo root):
    python scripts/dataset_tool.py index [--raw dataset/raw] [--phash-threshold 6]
    python scripts/dataset_tool.py split [--holdout-generators a,b] [--seed 42]
    python scripts/dataset_tool.py check
    python scripts/dataset_tool.py materialize [--out dataset]

Requires: pillow, imagehash, numpy, pandas.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

MANIFEST = Path("dataset/manifest.csv")
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
LABELS = {"real": 0, "ai": 1}
LABEL_NAMES = {0: "REAL", 1: "AI_GENERATED"}
SPLITS = ("train", "validation", "test", "test_unseen")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def popcount64(x: np.ndarray) -> np.ndarray:
    # Count set bits of uint64 values via byte view.
    return np.unpackbits(x.view(np.uint8).reshape(-1, 8), axis=1).sum(axis=1)


def near_duplicate_groups(phashes: np.ndarray, threshold: int) -> np.ndarray:
    """Union-find over pairs with Hamming distance <= threshold. Returns group index per row."""
    n = len(phashes)
    parent = np.arange(n)

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(n - 1):
        dist = popcount64(np.bitwise_xor(phashes[i + 1:], phashes[i]))
        for j in np.nonzero(dist <= threshold)[0] + i + 1:
            ri, rj = find(i), find(int(j))
            if ri != rj:
                parent[rj] = ri
    return np.array([find(i) for i in range(n)])


def cmd_index(args: argparse.Namespace) -> None:
    from PIL import Image
    import imagehash

    raw = Path(args.raw)
    rows, bad = [], []
    files = [p for p in raw.rglob("*") if p.suffix.lower() in IMAGE_EXTS]
    print(f"Found {len(files)} candidate files under {raw}")
    for i, p in enumerate(files, 1):
        rel = p.relative_to(raw).parts
        if len(rel) < 3 or rel[0] not in LABELS:
            bad.append((p, "not under raw/<real|ai>/<source>/"))
            continue
        try:
            with Image.open(p) as im:
                im.verify()
            with Image.open(p) as im:
                fmt = im.format
                w, h = im.size
                ph = imagehash.phash(im.convert("RGB"))
        except Exception as e:  # corrupt / unsupported
            bad.append((p, repr(e)))
            continue
        label = LABELS[rel[0]]
        rows.append({
            "path": p.as_posix(),
            "label": label,
            "label_name": LABEL_NAMES[label],
            "source": rel[1],
            "generator": rel[1] if label == 1 else "none",
            "sha256": sha256_file(p),
            "phash": str(ph),
            "width": w,
            "height": h,
            "format": fmt,
        })
        if i % 500 == 0:
            print(f"  indexed {i}/{len(files)}")

    df = pd.DataFrame(rows)
    before = len(df)
    conflicting = df.groupby("sha256")["label"].nunique()
    conflicting = conflicting[conflicting > 1].index
    if len(conflicting):
        print(f"WARNING: {len(conflicting)} identical files appear under BOTH real and ai -> dropped entirely")
        df = df[~df["sha256"].isin(conflicting)]
    df = df.drop_duplicates("sha256").reset_index(drop=True)
    print(f"Exact duplicates removed: {before - len(df)}")

    ph = np.array([int(h, 16) for h in df["phash"]], dtype=np.uint64)
    groups = near_duplicate_groups(ph, args.phash_threshold)
    df["group_id"] = [f"g{g:06d}" for g in groups]
    mixed = df.groupby("group_id")["label"].nunique()
    if (mixed > 1).any():
        print(f"WARNING: {(mixed > 1).sum()} near-duplicate groups contain both REAL and AI images - inspect them")
    print(f"Near-duplicate groups: {df['group_id'].nunique()} for {len(df)} images")

    df["split"] = ""
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(MANIFEST, index=False)
    if bad:
        log = MANIFEST.with_name("rejected_files.csv")
        pd.DataFrame(bad, columns=["path", "reason"]).to_csv(log, index=False)
        print(f"Rejected {len(bad)} files -> {log}")
    print(f"Wrote {MANIFEST}")


def cmd_split(args: argparse.Namespace) -> None:
    df = pd.read_csv(MANIFEST)
    if (df["split"].fillna("").isin(["test", "test_unseen"])).any() and not args.force:
        sys.exit("Manifest already has a test split. Re-splitting would contaminate it. Use --force only before any model work.")
    rng = np.random.default_rng(args.seed)
    holdout = {g.strip() for g in args.holdout_generators.split(",") if g.strip()}
    df["split"] = ""
    # A group touching a held-out generator goes wholly to test_unseen.
    unseen_groups = set(df.loc[df["generator"].isin(holdout), "group_id"])
    df.loc[df["group_id"].isin(unseen_groups), "split"] = "test_unseen"

    fractions = (args.train, args.val, 1 - args.train - args.val)
    rest = df[df["split"] == ""]
    # Whole groups are assigned; stratify by each group's majority label so mixed groups never span splits.
    group_label = rest.groupby("group_id")["label"].agg(lambda s: int(s.mean() >= 0.5))
    sizes = rest.groupby("group_id").size()
    assignment = {}
    for label in (0, 1):
        groups = group_label[group_label == label].index.to_numpy()
        order = rng.permutation(groups)
        total, cum = sizes[groups].sum(), 0
        for g in order:
            frac = cum / total
            assignment[g] = "train" if frac < fractions[0] else "validation" if frac < fractions[0] + fractions[1] else "test"
            cum += sizes[g]
    df.loc[rest.index, "split"] = rest["group_id"].map(assignment)
    df.to_csv(MANIFEST, index=False)
    print(df.groupby(["split", "label_name"]).size().unstack(fill_value=0))


def cmd_check(args: argparse.Namespace) -> None:
    df = pd.read_csv(MANIFEST)
    problems = []
    if (df["split"].fillna("") == "").any():
        problems.append(f"{(df['split'].fillna('') == '').sum()} rows have no split")
    for col in ("sha256", "group_id"):
        n = df.groupby(col)["split"].nunique()
        if (n > 1).any():
            problems.append(f"{(n > 1).sum()} {col} values appear in more than one split")
    ph = np.array([int(h, 16) for h in df["phash"]], dtype=np.uint64)
    splits = df["split"].to_numpy()
    cross = 0
    for i in range(len(df) - 1):
        dist = popcount64(np.bitwise_xor(ph[i + 1:], ph[i]))
        close = np.nonzero(dist <= args.phash_threshold)[0] + i + 1
        cross += int((splits[close] != splits[i]).sum())
    if cross:
        problems.append(f"{cross} near-duplicate pairs cross split boundaries")

    print("Counts (split x label):")
    print(df.groupby(["split", "label_name"]).size().unstack(fill_value=0))
    print("\nCounts (split x generator):")
    print(df.groupby(["split", "generator"]).size().unstack(fill_value=0))
    print("\nFormats per label:")
    print(df.groupby(["label_name", "format"]).size().unstack(fill_value=0))
    print("\nMedian resolution per label:")
    print(df.groupby("label_name")[["width", "height"]].median())
    for split, sub in df[df["split"].isin(["train", "validation", "test"])].groupby("split"):
        ai_share = sub["label"].mean()
        if abs(ai_share - 0.5) > 0.05:
            print(f"WARNING: {split} is {ai_share:.1%} AI (imbalanced)")
    print(f"\nDataset version (manifest sha256): {sha256_file(MANIFEST)[:16]}")
    if problems:
        print("\nLEAKAGE / INTEGRITY PROBLEMS:")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print("\nOK: no leakage detected.")


def cmd_materialize(args: argparse.Namespace) -> None:
    df = pd.read_csv(MANIFEST)
    out = Path(args.out)
    for row in df.itertuples():
        dst = out / row.split / row.label_name / f"{row.sha256[:16]}{Path(row.path).suffix.lower()}"
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(row.path, dst)
    print(f"Copied {len(df)} files into {out}/<split>/<label>/")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("index"); p.add_argument("--raw", default="dataset/raw"); p.add_argument("--phash-threshold", type=int, default=6)
    p = sub.add_parser("split")
    p.add_argument("--holdout-generators", default="")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--train", type=float, default=0.70)
    p.add_argument("--val", type=float, default=0.15)
    p.add_argument("--force", action="store_true")
    p = sub.add_parser("check"); p.add_argument("--phash-threshold", type=int, default=6)
    p = sub.add_parser("materialize"); p.add_argument("--out", default="dataset")
    args = ap.parse_args()
    {"index": cmd_index, "split": cmd_split, "check": cmd_check, "materialize": cmd_materialize}[args.cmd](args)


if __name__ == "__main__":
    main()
