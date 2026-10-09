"""RQ4: how do compression and simple edits affect the frozen ensemble? Validation split only.

    python scripts/robustness.py [--split validation] [--manifest ...]

Each perturbation is applied to every image (both classes) before scoring with the installed ensemble:
JPEG re-compression at several qualities, downscaling, a center crop and a screenshot-like PNG round trip at half size.
Writes evaluation/results/<run_id>/{robustness.csv, robustness.md, predictions_<perturbation>.csv}.
"""
from __future__ import annotations

import argparse
import io
import json

import pandas as pd
from PIL import Image

from common import ENSEMBLE_CONFIG, MANIFEST, ROOT, dataset_version, load_split, new_run_id, resolve


def jpeg(q: int):
    def f(im: Image.Image) -> Image.Image:
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=q)
        return Image.open(io.BytesIO(buf.getvalue())).convert("RGB")
    return f


def scale(s: float):
    def f(im: Image.Image) -> Image.Image:
        return im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.BICUBIC)
    return f


def center_crop(frac: float):
    def f(im: Image.Image) -> Image.Image:
        w, h = round(im.width * frac), round(im.height * frac)
        left, top = (im.width - w) // 2, (im.height - h) // 2
        return im.crop((left, top, left + w, top + h))
    return f


def screenshot(im: Image.Image) -> Image.Image:
    small = scale(0.5)(im)
    buf = io.BytesIO()
    small.save(buf, format="PNG")
    return Image.open(io.BytesIO(buf.getvalue())).convert("RGB")


PERTURBATIONS = {
    "original": lambda im: im,
    "jpeg_q90": jpeg(90), "jpeg_q70": jpeg(70), "jpeg_q50": jpeg(50), "jpeg_q30": jpeg(30),
    "downscale_0.5": scale(0.5), "downscale_0.25": scale(0.25),
    "center_crop_0.6": center_crop(0.6),
    "screenshot_png_0.5": screenshot,
}


def main() -> None:
    import torch
    from app.models.detector import build_detector, resolve_device
    from app.models.ensemble import combine
    from app.services.preprocessing import to_rgb
    from evaluation.metrics import evaluate

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(ENSEMBLE_CONFIG))
    ap.add_argument("--split", default="validation")
    ap.add_argument("--manifest")
    ap.add_argument("--batch-size", type=int, default=16)
    args = ap.parse_args()

    manifest = resolve(args.manifest) if args.manifest else MANIFEST
    df = load_split(args.split, manifest=manifest)
    config = json.loads(resolve(args.config).read_text())
    device = resolve_device("auto")
    detectors = [build_detector(m, device) for m in config["members"]]
    weights = {m["name"]: m.get("weight", 1.0) for m in config["members"]}

    out = ROOT / "evaluation" / "results" / new_run_id(f"robustness-{config['version']}")
    out.mkdir(parents=True)
    rows = []
    for name, perturb in PERTURBATIONS.items():
        probs = []
        for start in range(0, len(df), args.batch_size):
            images = []
            for p in df["path"].iloc[start:start + args.batch_size]:
                with Image.open(resolve(p)) as im:
                    images.append(perturb(to_rgb(im)))
            with torch.no_grad():
                scores = {d.name: d.predict(images) for d in detectors}
            probs += [combine({n: float(scores[n][i]) for n in scores}, weights, config["method"],
                              config.get("calibration"), config.get("intercept", 0.0)) for i in range(len(images))]
        preds = df[["path", "label", "generator", "split"]].assign(model=f"{config['version']}+{name}",
                                                                   ai_probability=probs)
        preds.to_csv(out / f"predictions_{name}.csv", index=False)
        res = evaluate(preds, config["t_low"], config["t_high"])
        b, u = res["binary@0.5"], res.get("thresholded", {})
        rows.append({"perturbation": name, "accuracy": b["accuracy"], "f1": b["f1"], "fpr": b["fpr"], "fnr": b["fnr"],
                     "roc_auc": b["roc_auc"], "coverage": u.get("coverage"), "decided_accuracy": u.get("decided", {}).get("accuracy")})
        print(f"{name:20} acc {b['accuracy']:.4f} FPR {b['fpr']:.4f} FNR {b['fnr']:.4f} AUC {b['roc_auc']:.4f}")

    table = pd.DataFrame(rows)
    table.to_csv(out / "robustness.csv", index=False)
    (out / "robustness.md").write_text(
        f"# Robustness ({config['version']}, {args.split}, n = {len(df)}, dataset {dataset_version(manifest)})\n\n"
        + "| " + " | ".join(table.columns) + " |\n|" + "---|" * len(table.columns) + "\n"
        + "".join("| " + " | ".join(v if isinstance(v, str) else f"{v:.4f}" for v in r) + " |\n"
                  for r in table.itertuples(index=False)), encoding="utf-8")
    print(f"\nResults in {out}")


if __name__ == "__main__":
    main()
