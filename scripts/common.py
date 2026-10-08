"""Helpers shared by the pipeline scripts. Makes the backend package importable so scripts reuse the exact
same detector, ensemble and preprocessing code as the API."""
from __future__ import annotations

import hashlib
import random
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))

MANIFEST = ROOT / "dataset" / "manifest.csv"
ENSEMBLE_CONFIG = ROOT / "models" / "ensemble" / "ensemble_config.json"
SEALED_SPLITS = {"test", "test_unseen"}


def load_split(split: str, final: bool = False, manifest: Path = MANIFEST) -> pd.DataFrame:
    """Rows of one split. Sealed test splits need final=True (only the final evaluation passes it)."""
    if split in SEALED_SPLITS and not final:
        sys.exit(f"Refusing to read the sealed '{split}' split. Tune on 'validation'; "
                 "only scripts/final_evaluation.py may touch test data.")
    df = pd.read_csv(manifest)
    out = df[df["split"] == split].reset_index(drop=True)
    if out.empty:
        sys.exit(f"No rows with split == {split!r} in {manifest}")
    return out


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dataset_version(manifest: Path = MANIFEST) -> str:
    return file_sha256(manifest)[:16]


def new_run_id(name: str) -> str:
    return f"{datetime.now():%Y%m%d-%H%M%S}-{name}"


def seed_everything(seed: int) -> None:
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def resolve(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p
