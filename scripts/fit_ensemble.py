"""Fit ensemble weights, calibration and UNCERTAIN thresholds on VALIDATION predictions.

    python scripts/evaluate.py --run-name val-members                 # produces predictions.csv with score_<member>
    python scripts/fit_ensemble.py evaluation/results/<run_id> --version ensemble-v2 [--write]

Prints a strategy comparison and threshold search; with --write it updates models/ensemble/ensemble_config.json
(old config backed up). Plots + report go to evaluation/results/ensemble/<version>/.
"""
from __future__ import annotations

import argparse
import itertools
import json
import shutil
from datetime import date

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from common import ENSEMBLE_CONFIG, ROOT, dataset_version, resolve

TARGETS = {"accuracy": 0.95, "fpr": 0.05, "fnr": 0.05}


def logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def summarize(name, y, p):
    from evaluation.metrics import binary_metrics

    m = binary_metrics(y, p)
    return {"strategy": name, "accuracy": m["accuracy"], "f1": m["f1"], "fpr": m["fpr"], "fnr": m["fnr"],
            "roc_auc": m["roc_auc"], "log_loss": log_loss(y, np.clip(p, 1e-6, 1 - 1e-6)), "brier": brier_score_loss(y, p)}


def search_weights(y, S, step):
    """Maximize ROC-AUC; ties (common when members are strong) are broken by lower log-loss."""
    best, best_w = (-1.0, -np.inf), None
    grid = np.arange(0, 1 + 1e-9, step)
    for w in itertools.product(grid, repeat=S.shape[1] - 1):
        if sum(w) > 1 + 1e-9:
            continue
        weights = np.array([*w, 1 - sum(w)])
        p = S @ weights
        key = (round(roc_auc_score(y, p), 6), -log_loss(y, np.clip(p, 1e-6, 1 - 1e-6)))
        if key > best:
            best, best_w = key, weights
    return best_w


def platt(y, p, seed):
    """Cross-fitted calibrated probabilities (for honest reporting) + parameters fitted on all rows."""
    x = logit(p).reshape(-1, 1)
    lr = LogisticRegression(C=1e6)
    cv = StratifiedKFold(5, shuffle=True, random_state=seed)
    crossfit = cross_val_predict(lr, x, y, cv=cv, method="predict_proba")[:, 1]
    lr.fit(x, y)
    return crossfit, {"type": "platt", "a": float(lr.coef_[0, 0]), "b": float(lr.intercept_[0])}


def threshold_search(y, p, step=0.01):
    from evaluation.metrics import threshold_metrics

    rows = []
    for t_low in np.arange(0.02, 0.5 + 1e-9, step):
        for t_high in np.arange(0.5, 0.98 + 1e-9, step):
            m = threshold_metrics(y, p, round(float(t_low), 2), round(float(t_high), 2))
            d = m.get("decided")
            if not d:
                continue
            rows.append({"t_low": m["t_low"], "t_high": m["t_high"], "coverage": m["coverage"],
                         "accuracy": d["accuracy"], "fpr": d["fpr"], "fnr": d["fnr"]})
    table = pd.DataFrame(rows)
    ok = table[(table.accuracy >= TARGETS["accuracy"]) & (table.fpr < TARGETS["fpr"]) & (table.fnr < TARGETS["fnr"])]
    if len(ok):
        # Among equally good pairs prefer the widest uncertainty band: safer on images unlike the validation set.
        ok = ok.assign(width=ok.t_high - ok.t_low)
        choice = ok.sort_values(["coverage", "accuracy", "width"], ascending=False).iloc[0]
        met = True
    else:
        choice = table[table.coverage >= 0.7].sort_values("accuracy", ascending=False).iloc[0]
        met = False
    return table, choice, met


def plots(y, p, table, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    frontier = table.groupby(table.coverage.round(2))["accuracy"].max().sort_index()
    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.plot(frontier.index, frontier.values)
    ax.set_xlabel("Coverage (share of images given a definite answer)"); ax.set_ylabel("Accuracy on decided images")
    ax.set_title("Risk-coverage (validation)"); fig.tight_layout(); fig.savefig(out / "risk_coverage.png", dpi=140); plt.close(fig)

    bins = np.linspace(0, 1, 11)
    idx = np.clip(np.digitize(p, bins) - 1, 0, 9)
    centers, freq = [], []
    for b in range(10):
        if (idx == b).any():
            centers.append(p[idx == b].mean()); freq.append(y[idx == b].mean())
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.plot([0, 1], [0, 1], "--", color="gray"); ax.plot(centers, freq, "o-")
    ax.set_xlabel("Predicted AI probability"); ax.set_ylabel("Observed share AI"); ax.set_title("Reliability (validation)")
    fig.tight_layout(); fig.savefig(out / "reliability.png", dpi=140); plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir", help="evaluation/results/<run_id> from scripts/evaluate.py on validation")
    ap.add_argument("--config", default=str(ENSEMBLE_CONFIG))
    ap.add_argument("--version", required=True, help="new version string, e.g. ensemble-v2")
    ap.add_argument("--weight-step", type=float, default=0.05)
    ap.add_argument("--no-calibration", action="store_true")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--write", action="store_true", help="write the new ensemble_config.json")
    args = ap.parse_args()

    run_dir = resolve(args.run_dir)
    df = pd.read_csv(run_dir / "predictions.csv")
    if set(df["split"]) != {"validation"}:
        raise SystemExit("Ensemble fitting must use validation predictions only.")
    config = json.loads(resolve(args.config).read_text())
    names = [m["name"] for m in config["members"]]
    S = df[[f"score_{n}" for n in names]].to_numpy()
    y = df["label"].to_numpy().astype(int)

    results = [summarize(n, y, S[:, i]) for i, n in enumerate(names)]
    results.append(summarize("mean", y, S.mean(axis=1)))
    weights = search_weights(y, S, args.weight_step) if len(names) > 1 else np.array([1.0])
    weighted = S @ weights
    results.append(summarize("weighted_average", y, weighted))
    results.append(summarize("majority_vote", y, (S >= 0.5).mean(axis=1)))
    if len(names) > 1:
        stack = cross_val_predict(LogisticRegression(), logit(S), y,
                                  cv=StratifiedKFold(5, shuffle=True, random_state=args.seed), method="predict_proba")[:, 1]
        results.append(summarize("stacking (report only)", y, stack))
    comparison = pd.DataFrame(results)
    print(comparison.round(4).to_string(index=False))

    calibration = None
    final_p = weighted
    if not args.no_calibration:
        final_p, calibration = platt(y, weighted, args.seed)
        print(f"\nPlatt calibration a={calibration['a']:.3f} b={calibration['b']:.3f}; "
              f"Brier {brier_score_loss(y, weighted):.4f} -> {brier_score_loss(y, final_p):.4f} (cross-fitted)")

    table, choice, met = threshold_search(y, final_p)
    print(f"\nChosen thresholds t_low={choice.t_low} t_high={choice.t_high}: coverage {choice.coverage:.3f}, "
          f"decided accuracy {choice.accuracy:.4f}, FPR {choice.fpr:.4f}, FNR {choice.fnr:.4f}")
    if not met:
        print("WARNING: no threshold pair met the targets (acc>=95%, FPR<5%, FNR<5%); "
              "chose best accuracy at >=70% coverage. Improve the detectors before trusting this.")

    out = ROOT / "evaluation" / "results" / "ensemble" / args.version
    out.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(out / "strategy_comparison.csv", index=False)
    table.to_csv(out / "threshold_search.csv", index=False)
    plots(y, final_p, table, out)

    new_config = {
        "version": args.version,
        "method": "weighted_average",
        "members": [{**m, "weight": round(float(w), 4)} for m, w in zip(config["members"], weights)],
        "calibration": calibration,
        "t_low": float(choice.t_low),
        "t_high": float(choice.t_high),
        "fitted_on": {"run": run_dir.name, "split": "validation", "n": int(len(df)), "dataset_version": dataset_version(),
                      "targets_met": bool(met), "date": date.today().isoformat()},
    }
    (out / "ensemble_config.json").write_text(json.dumps(new_config, indent=2))
    print(f"\nReport files in {out}")
    if args.write:
        target = resolve(args.config)
        shutil.copy2(target, target.with_name(f"ensemble_config.{config['version']}.bak.json"))
        target.write_text(json.dumps(new_config, indent=2))
        print(f"Wrote {target} (previous version backed up)")


if __name__ == "__main__":
    main()
