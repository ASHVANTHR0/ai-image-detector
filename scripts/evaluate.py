"""Run every detector in an ensemble config (and the ensemble itself) over one dataset split.

    python scripts/evaluate.py                              # validation split, models/ensemble/ensemble_config.json
    python scripts/evaluate.py --config my_candidates.json --run-name baseline
    python scripts/evaluate.py --member detector_a          # only some members

Writes evaluation/results/<run_id>/:
    predictions.csv              ensemble scores (+ score_<member> columns), roadmap format
    predictions_<member>.csv     one file per member
    run_info.json                model ids, device, timing, memory, dataset version
    metrics_<name>.md/json       via evaluation/metrics.py
"""
from __future__ import annotations

import argparse
import json
import platform
import time

import numpy as np
from PIL import Image
from tqdm import tqdm

from common import ENSEMBLE_CONFIG, MANIFEST, ROOT, dataset_version, load_split, new_run_id, resolve


def run(df, detectors, batch_size: int) -> tuple[dict[str, np.ndarray], dict[str, float]]:
    from app.services.preprocessing import to_rgb

    scores = {d.name: np.zeros(len(df)) for d in detectors}
    seconds = {d.name: 0.0 for d in detectors}
    for start in tqdm(range(0, len(df), batch_size), desc="batches"):
        rows = df.iloc[start:start + batch_size]
        images = []
        for p in rows["path"]:
            with Image.open(resolve(p)) as im:
                images.append(to_rgb(im))
        for d in detectors:
            t0 = time.perf_counter()
            scores[d.name][start:start + len(rows)] = d.predict(images)
            seconds[d.name] += time.perf_counter() - t0
    return scores, {n: 1000 * s / len(df) for n, s in seconds.items()}


def main() -> None:
    import torch
    from app.models.detector import build_detector, resolve_device
    from app.models.ensemble import combine
    from evaluation.metrics import evaluate, to_markdown

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(ENSEMBLE_CONFIG))
    ap.add_argument("--split", default="validation")
    ap.add_argument("--manifest", help="alternative manifest CSV (e.g. dataset/benchmark/manifest.csv)")
    ap.add_argument("--member", action="append", help="evaluate only these members")
    ap.add_argument("--run-name", default="eval")
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--device", default="auto")
    ap.add_argument("--limit", type=int, help="evaluate a random subset (quick checks)")
    ap.add_argument("--final", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args()

    config = json.loads(resolve(args.config).read_text())
    members = [m for m in config["members"] if not args.member or m["name"] in args.member]
    df = load_split(args.split, final=args.final, manifest=resolve(args.manifest) if args.manifest else MANIFEST)
    if args.limit:
        df = df.sample(n=min(args.limit, len(df)), random_state=42).reset_index(drop=True)

    device = resolve_device(args.device)
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats()
    detectors = [build_detector(m, device) for m in members]
    scores, ms_per_image = run(df, detectors, args.batch_size)

    run_id = new_run_id(args.run_name)
    out = ROOT / "evaluation" / "results" / run_id
    out.mkdir(parents=True)
    base = df[["path", "label", "generator", "split"]].copy()
    summary = {}
    for name, s in scores.items():
        preds = base.assign(model=name, ai_probability=s)
        preds.to_csv(out / f"predictions_{name}.csv", index=False)
        summary[name] = evaluate(preds, config.get("t_low"), config.get("t_high"))
        means = preds.groupby("label")["ai_probability"].mean()
        if len(means) == 2 and means[1] <= means[0]:
            print(f"WARNING: {name} scores REAL images higher than AI images - check its label mapping (ai_label)")

    if len(members) == len(config["members"]):
        weights = {m["name"]: m.get("weight", 1.0) for m in members}
        ensemble_p = [combine({n: float(scores[n][i]) for n in scores}, weights, config.get("method", "weighted_average"),
                              config.get("calibration")) for i in range(len(df))]
        preds = base.assign(model=config["version"], ai_probability=ensemble_p,
                            **{f"score_{n}": s for n, s in scores.items()})
        preds.to_csv(out / "predictions.csv", index=False)
        summary[config["version"]] = evaluate(preds, config.get("t_low"), config.get("t_high"))

    for name, res in summary.items():
        (out / f"metrics_{name}.json").write_text(json.dumps(res, indent=2))
        (out / f"metrics_{name}.md").write_text(to_markdown(res, None, None), encoding="utf-8")

    info = {
        "run_id": run_id, "split": args.split, "n_images": len(df), "dataset_version": dataset_version(resolve(args.manifest) if args.manifest else MANIFEST),
        "manifest": args.manifest or "dataset/manifest.csv",
        "config": args.config, "members": members, "device": str(device),
        "gpu": torch.cuda.get_device_name(0) if device.type == "cuda" else None,
        "peak_gpu_memory_mb": round(torch.cuda.max_memory_allocated() / 2 ** 20) if device.type == "cuda" else None,
        "ms_per_image": {k: round(v, 2) for k, v in ms_per_image.items()},
        "batch_size": args.batch_size, "python": platform.python_version(), "torch": torch.__version__,
    }
    (out / "run_info.json").write_text(json.dumps(info, indent=2))

    print(f"\nResults in {out}")
    print(f"{'model':28} {'acc':>7} {'prec':>7} {'recall':>7} {'f1':>7} {'fpr':>7} {'auc':>7} {'ms/img':>7}")
    for name, res in summary.items():
        b = res["binary@0.5"]
        ms = ms_per_image.get(name, sum(ms_per_image.values()))
        print(f"{name:28} {b['accuracy']:7.4f} {b['precision']:7.4f} {b['recall']:7.4f} {b['f1']:7.4f} "
              f"{b['fpr']:7.4f} {b['roc_auc']:7.4f} {ms:7.1f}")


if __name__ == "__main__":
    main()
