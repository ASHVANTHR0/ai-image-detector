"""Collect a training set from OpenFake's *train* split (ComplexDataLab/OpenFake, CC BY-NC 4.0).

    python scripts/fetch_training_data.py [--row-groups 90] [--workers 4]

OpenFake keeps its train generators separate from its test generators, so a model trained here and scored on
dataset/benchmark (built from the test split) is measured on generators it has never seen.

Every image is processed identically, whatever its class: converted to RGB, downscaled to at most --max-side pixels,
and saved as JPEG (quality 95). This removes the "PNG = AI / JPEG = real" and resolution shortcuts. Images whose
SHA-256 appears in the benchmark manifest are skipped. Output goes to dataset/raw/real/openfake-<source>/ and
dataset/raw/ai/openfake-<generator>/; then build the training manifest with scripts/dataset_tool.py.
"""
from __future__ import annotations

import argparse
import hashlib
import io
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import pyarrow.parquet as pq
from huggingface_hub import HfFileSystem
from PIL import Image, ImageOps

from common import ROOT

BASE = "datasets/ComplexDataLab/OpenFake/core"
RAW = ROOT / "dataset" / "raw"


def normalize(data: bytes, max_side: int) -> bytes:
    with Image.open(io.BytesIO(data)) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode in ("RGBA", "LA", "P"):
            rgba = im.convert("RGBA")
            bg = Image.new("RGB", rgba.size, (255, 255, 255))
            bg.paste(rgba, mask=rgba.getchannel("A"))
            im = bg
        im = im.convert("RGB")
        if max(im.size) > max_side:
            im.thumbnail((max_side, max_side), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=95)
        return buf.getvalue()


def fetch(fs: HfFileSystem, file: str, rg: int, max_side: int, banned: set[str]) -> list[dict]:
    with fs.open(file, block_size=64 << 20) as fh:
        table = pq.ParquetFile(fh).read_row_group(rg, columns=["image", "label", "model"]).to_pandas()
    out = []
    for r in table.itertuples():
        raw = r.image["bytes"]
        if hashlib.sha256(raw).hexdigest() in banned:
            continue
        try:
            data = normalize(raw, max_side)
        except Exception:
            continue
        is_ai = r.label != "real"
        folder = RAW / ("ai" if is_ai else "real") / f"openfake-{r.model}"
        folder.mkdir(parents=True, exist_ok=True)
        sha = hashlib.sha256(data).hexdigest()
        (folder / f"{sha[:16]}.jpg").write_bytes(data)
        out.append({"label": int(is_ai), "model": r.model})
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--row-groups", type=int, default=90, help="~69 images each")
    ap.add_argument("--max-side", type=int, default=1024)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    bench = ROOT / "dataset" / "benchmark" / "manifest.csv"
    banned = set(pd.read_csv(bench)["sha256"]) if bench.exists() else set()
    fs = HfFileSystem()
    files = sorted(f for f in fs.ls(BASE, detail=False) if "/train-" in f)
    # Spread picks over all files; row group index varies so different parts of each file are used.
    step = len(files) / args.row_groups
    picks = [(files[int(i * step)], (i * 13) % 50) for i in range(args.row_groups)]
    print(f"Fetching {len(picks)} row groups from {len(files)} train files", flush=True)

    rows, done = [], 0
    with ThreadPoolExecutor(args.workers) as pool:
        futures = {pool.submit(fetch, HfFileSystem(), f, rg, args.max_side, banned): (f, rg) for f, rg in picks}
        for fut in as_completed(futures):
            done += 1
            try:
                rows += fut.result()
            except Exception as exc:  # e.g. a file with fewer row groups; skip it
                print(f"  skipped {futures[fut][0].split('/')[-1]} rg {futures[fut][1]}: {type(exc).__name__}", flush=True)
            if done % 10 == 0 or done == len(picks):
                print(f"  {done}/{len(picks)} row groups, {len(rows)} images", flush=True)

    df = pd.DataFrame(rows)
    print(df.groupby("label").size().rename({0: "REAL", 1: "AI"}).to_string())
    print(f"{df[df.label == 1].model.nunique()} generators, real sources: {sorted(df[df.label == 0].model.unique())}")


if __name__ == "__main__":
    main()
