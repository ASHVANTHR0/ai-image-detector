"""Download a small, balanced benchmark sample from OpenFake (ComplexDataLab/OpenFake, CC BY-NC 4.0) without
downloading whole multi-GB shards: only selected parquet row groups are read over HTTP.

    python scripts/fetch_benchmark.py [--core-groups 6] [--reddit-groups 2] [--per-model 15]

`core/test` uses generators that OpenFake keeps out of its own training split, paired with real photos from separate
sources. `reddit` is in-the-wild posts. Images go to dataset/benchmark/openfake/<set>/<real|ai>/ and a manifest is
written to dataset/benchmark/manifest.csv. Rows are split 50/50 per (set, label, generator) into
`validation` (used to choose models, weights and thresholds) and `holdout` (used only to report the result).
This benchmark is separate from dataset/manifest.csv and must never be used for training.
"""
from __future__ import annotations

import argparse
import hashlib
import io
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from huggingface_hub import HfFileSystem
from PIL import Image

from common import ROOT

OUT = ROOT / "dataset" / "benchmark"


def spread_row_groups(fs: HfFileSystem, files: list[str], n: int) -> list[tuple[str, int]]:
    """n (file, row group) pairs spread evenly over the files and over positions inside them."""
    files = sorted(files)
    picks = []
    for i in range(n):
        f = files[round(i * (len(files) - 1) / max(1, n - 1))] if n > 1 else files[0]
        groups = pq.ParquetFile(fs.open(f, block_size=1 << 20)).num_row_groups
        picks.append((f, int((i * 7919 + groups // 2) % groups)))  # vary the position, deterministically
    return list(dict.fromkeys(picks))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--core-groups", type=int, default=6, help="row groups (~150 images, ~100 MB each) from core/test")
    ap.add_argument("--reddit-groups", type=int, default=2, help="row groups from the in-the-wild reddit set")
    ap.add_argument("--per-model", type=int, default=15, help="max AI images per generator per set")
    ap.add_argument("--real-per-set", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    fs = HfFileSystem()
    base = "datasets/ComplexDataLab/OpenFake"
    rows = []
    for set_name, folder, n in [("core", "core", args.core_groups), ("reddit", "reddit", args.reddit_groups)]:
        files = [f for f in fs.ls(f"{base}/{folder}", detail=False) if f.endswith(".parquet") and "/test-" in f]
        for file, rg in spread_row_groups(fs, files, n):
            print(f"[{set_name}] reading {file.split('/')[-1]} row group {rg}", flush=True)
            with fs.open(file, block_size=128 << 20) as fh:
                table = pq.ParquetFile(fh).read_row_group(rg, columns=["image", "label", "model"]).to_pandas()
            table["set"] = set_name
            rows.append(table)
    data = pd.concat(rows, ignore_index=True)
    data["is_ai"] = data["label"] != "real"

    keep = []
    for set_name, sub in data.groupby("set"):
        ai = sub[sub.is_ai]
        for _, g in ai.groupby("model"):
            keep.append(g.sample(n=min(len(g), args.per_model), random_state=args.seed))
        n_ai = sum(len(k) for k in keep if (k["set"] == set_name).all())
        real = sub[~sub.is_ai]
        keep.append(real.sample(n=min(len(real), max(args.real_per_set, n_ai)), random_state=args.seed))
    sample = pd.concat(keep, ignore_index=True)

    records = []
    for r in sample.itertuples():
        data_bytes = r.image["bytes"]
        sha = hashlib.sha256(data_bytes).hexdigest()
        with Image.open(io.BytesIO(data_bytes)) as im:
            fmt = (im.format or "PNG").lower().replace("jpeg", "jpg")
            w, h = im.size
        label = 1 if r.is_ai else 0
        folder = OUT / "openfake" / r.set / ("ai" if label else "real")
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{sha[:16]}.{fmt}"
        path.write_bytes(data_bytes)
        records.append({"path": path.relative_to(ROOT).as_posix(), "label": label,
                        "label_name": "AI_GENERATED" if label else "REAL", "source": f"openfake-{r.set}",
                        "generator": r.model if label else "none", "real_source": "none" if label else r.model,
                        "set": r.set, "sha256": sha, "width": w, "height": h, "format": fmt.upper()})
    manifest = pd.DataFrame(records).drop_duplicates("sha256").reset_index(drop=True)

    # 50/50 per (set, label, generator) into validation / holdout
    manifest["split"] = "holdout"
    for _, g in manifest.groupby(["set", "label", "generator"]):
        idx = rng.permutation(g.index.to_numpy())
        manifest.loc[idx[: len(idx) // 2 + len(idx) % 2], "split"] = "validation"
    OUT.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(OUT / "manifest.csv", index=False)
    print(manifest.groupby(["set", "split", "label_name"]).size())
    print(f"{manifest.generator.nunique() - 1} AI generators; wrote {OUT / 'manifest.csv'}")


if __name__ == "__main__":
    main()
