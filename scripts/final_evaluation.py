"""Phase 9: freeze the pipeline and run the ONE-TIME evaluation on the sealed test splits.

    python scripts/final_evaluation.py --confirm

Steps: write evaluation/results/final/FREEZE.md (git commit, config + checkpoint + manifest hashes),
run the frozen ensemble on `test` and `test_unseen` with the same code the API uses, compute metrics with
bootstrap CIs and plots, write summary.json (served by /api/v1/evaluation) and record the result in the
model_versions table. Refuses to run twice unless --rerun-reason is given (the reason is logged).
"""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime

import pandas as pd

from common import ENSEMBLE_CONFIG, MANIFEST, ROOT, dataset_version, file_sha256, load_split, resolve

FINAL = ROOT / "evaluation" / "results" / "final"


def git_commit() -> str:
    try:
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
        return sha + (" (uncommitted changes present)" if dirty else "")
    except Exception:
        return "not a git repository"


def member_hashes(config: dict) -> dict:
    hashes = {}
    for m in config["members"]:
        folder = resolve(m["path"])
        files = [f for ext in ("*.safetensors", "*.bin", "*.pt") for f in sorted(folder.glob(ext))]
        hashes[m["name"]] = {f.name: file_sha256(f)[:16] for f in files}
    return hashes


def run_split(split: str, config: dict, batch_size: int) -> pd.DataFrame | None:
    from app.models.detector import build_detector, resolve_device
    from app.models.ensemble import combine
    from evaluate import run

    try:
        df = load_split(split, final=True)
    except SystemExit:
        print(f"No rows for split {split}, skipping")
        return None
    device = resolve_device("auto")
    detectors = [build_detector(m, device) for m in config["members"]]
    scores, ms = run(df, detectors, batch_size)
    weights = {m["name"]: m.get("weight", 1.0) for m in config["members"]}
    p = [combine({n: float(scores[n][i]) for n in scores}, weights, config.get("method", "weighted_average"),
                 config.get("calibration"), config.get("intercept", 0.0)) for i in range(len(df))]
    out = df[["path", "label", "generator", "split"]].assign(model=config["version"], ai_probability=p,
                                                             **{f"score_{n}": s for n, s in scores.items()})
    out.attrs["ms_per_image"] = sum(ms.values())
    return out


def main() -> None:
    from evaluation.metrics import evaluate, make_plots, to_markdown

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--confirm", action="store_true", help="required: you have frozen model, weights and thresholds")
    ap.add_argument("--rerun-reason")
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--bootstrap", type=int, default=1000)
    args = ap.parse_args()
    if not args.confirm:
        raise SystemExit("This is the one-time final test. Re-run with --confirm once everything is frozen.")
    if (FINAL / "summary.json").exists() and not args.rerun_reason:
        raise SystemExit("Final evaluation already exists. A rerun must be justified with --rerun-reason "
                         "(and the earlier result must still be reported).")

    config = json.loads(ENSEMBLE_CONFIG.read_text())
    FINAL.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().isoformat(timespec="seconds")
    freeze = [f"# Freeze record - {stamp}", "",
              f"- Git commit: {git_commit()}",
              f"- Ensemble config: {config['version']} sha256 {file_sha256(ENSEMBLE_CONFIG)[:16]}",
              f"- Thresholds: t_low={config['t_low']}, t_high={config['t_high']}",
              f"- Members: {json.dumps(member_hashes(config))}",
              f"- Dataset version (manifest sha256): {dataset_version()}",
              "- Pre-registered metrics: accuracy, precision, recall, F1, specificity, FPR, FNR, ROC-AUC (95% bootstrap CI), "
              "confusion matrix, coverage/uncertain rate, per-generator accuracy, ms/image; splits: test, test_unseen.", ""]
    if args.rerun_reason:
        freeze.append(f"- RERUN reason: {args.rerun_reason}")
    with (FINAL / "FREEZE.md").open("a", encoding="utf-8") as f:
        f.write("\n".join(freeze) + "\n")

    summary = {"model": config["version"], "date": stamp, "dataset_version": dataset_version(),
               "thresholds": {"t_low": config["t_low"], "t_high": config["t_high"]}, "splits": {}}
    for split in ("test", "test_unseen"):
        preds = run_split(split, config, args.batch_size)
        if preds is None:
            continue
        out = FINAL / split
        out.mkdir(exist_ok=True)
        preds.to_csv(out / "predictions.csv", index=False)
        res = evaluate(preds, config["t_low"], config["t_high"], args.bootstrap)
        by_gen = {str(g): evaluate(sub, config["t_low"], config["t_high"]) for g, sub in preds.groupby("generator")}
        res["by_generator"] = by_gen
        (out / "metrics.json").write_text(json.dumps(res, indent=2))
        (out / "metrics.md").write_text(to_markdown(res, by_gen, "generator"), encoding="utf-8")
        make_plots(preds, res, out)
        b = res["binary@0.5"]
        summary["splits"][split] = {
            **{k: b[k] for k in ("n", "accuracy", "precision", "recall", "f1", "specificity", "fpr", "fnr", "roc_auc")},
            "ci95": b.get("ci95"), "confusion_matrix": b["confusion_matrix"],
            "coverage": res["thresholded"]["coverage"], "decided": res["thresholded"].get("decided"),
            "by_generator": {g: {"n": r["binary@0.5"]["n"], "accuracy": r["binary@0.5"]["accuracy"]} for g, r in by_gen.items()},
            "confidence_histogram": pd.cut(preds["ai_probability"], [i / 10 for i in range(11)], include_lowest=True)
                                      .value_counts(sort=False).tolist(),
            "ms_per_image": preds.attrs.get("ms_per_image"),
        }
        print(f"{split}: acc {b['accuracy']:.4f} P {b['precision']:.4f} R {b['recall']:.4f} F1 {b['f1']:.4f} "
              f"FPR {b['fpr']:.4f} FNR {b['fnr']:.4f} AUC {b['roc_auc']:.4f}")
    (FINAL / "summary.json").write_text(json.dumps(summary, indent=2))

    if "test" in summary["splits"]:
        from app.config import get_settings
        from app.database.database import ModelVersion, make_session_factory

        t = summary["splits"]["test"]
        with make_session_factory(get_settings().database_url)() as session:
            session.add(ModelVersion(model_name="ensemble", version=config["version"], accuracy=t["accuracy"],
                                     precision=t["precision"], recall=t["recall"], f1_score=t["f1"]))
            session.commit()
    print(f"Final results in {FINAL}. Write the interpretation in {FINAL / 'RESULTS.md'}.")


if __name__ == "__main__":
    main()
