"""Shared metrics for the AI image detector project.

Input: predictions.csv with at least `label` (0=REAL, 1=AI_GENERATED) and `ai_probability`.

    python metrics.py preds.csv [--t-low 0.1 --t-high 0.9] [--by generator]
                      [--bootstrap 1000] [--out-dir DIR] [--plots]

Importable: `from metrics import binary_metrics, threshold_metrics`.
Requires: numpy, pandas, scikit-learn (+ matplotlib for --plots).
"""
from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


def _safe_div(a: float, b: float) -> float:
    return float(a / b) if b else float("nan")


def binary_metrics(y: np.ndarray, p: np.ndarray, threshold: float = 0.5) -> dict:
    """Forced binary decision: AI if p >= threshold. Positive class = AI."""
    y = np.asarray(y).astype(int)
    pred = (np.asarray(p) >= threshold).astype(int)
    tp = int(((pred == 1) & (y == 1)).sum())
    tn = int(((pred == 0) & (y == 0)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    out = {
        "n": int(len(y)),
        "accuracy": _safe_div(tp + tn, len(y)),
        "precision": precision,
        "recall": recall,
        "f1": _safe_div(2 * precision * recall, precision + recall) if tp else 0.0,
        "specificity": _safe_div(tn, tn + fp),
        "fpr": _safe_div(fp, fp + tn),
        "fnr": _safe_div(fn, fn + tp),
        "confusion_matrix": {"TN": tn, "FP": fp, "FN": fn, "TP": tp},
    }
    out["roc_auc"] = float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else float("nan")
    return out


def threshold_metrics(y: np.ndarray, p: np.ndarray, t_low: float, t_high: float) -> dict:
    """Three-way decision: AI if p >= t_high, REAL if p <= t_low, else UNCERTAIN."""
    y, p = np.asarray(y).astype(int), np.asarray(p)
    decided = (p >= t_high) | (p <= t_low)
    out = {
        "t_low": t_low,
        "t_high": t_high,
        "coverage": float(decided.mean()) if len(p) else float("nan"),
        "uncertain_rate": float((~decided).mean()) if len(p) else float("nan"),
        "uncertain_rate_real": float((~decided[y == 0]).mean()) if (y == 0).any() else float("nan"),
        "uncertain_rate_ai": float((~decided[y == 1]).mean()) if (y == 1).any() else float("nan"),
    }
    if decided.any():
        decided_m = binary_metrics(y[decided], p[decided], threshold=0.5)
        decided_m.pop("roc_auc", None)
        out["decided"] = decided_m
    return out


def bootstrap_ci(y, p, n_boot: int, seed: int = 42, threshold: float = 0.5) -> dict:
    rng = np.random.default_rng(seed)
    y, p = np.asarray(y), np.asarray(p)
    keys = ["accuracy", "precision", "recall", "f1", "fpr", "fnr", "roc_auc"]
    samples = {k: [] for k in keys}
    for _ in range(n_boot):
        idx = rng.integers(0, len(y), len(y))
        m = binary_metrics(y[idx], p[idx], threshold)
        for k in keys:
            samples[k].append(m[k])
    with warnings.catch_warnings():  # metrics undefined for one-class resamples are NaN, which is expected
        warnings.simplefilter("ignore", RuntimeWarning)
        return {k: [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))] for k, v in samples.items()}


def evaluate(df: pd.DataFrame, t_low=None, t_high=None, n_boot=0) -> dict:
    y, p = df["label"].to_numpy(), df["ai_probability"].to_numpy()
    res = {"binary@0.5": binary_metrics(y, p)}
    if n_boot:
        res["binary@0.5"]["ci95"] = bootstrap_ci(y, p, n_boot)
    if t_low is not None and t_high is not None:
        res["thresholded"] = threshold_metrics(y, p, t_low, t_high)
    return res


def to_markdown(results: dict, by_results: dict | None, by: str | None) -> str:
    b = results["binary@0.5"]
    lines = ["## Overall (forced binary, threshold 0.5)", "", "| Metric | Value | 95% CI |", "|---|---|---|"]
    ci = b.get("ci95", {})
    for k in ["accuracy", "precision", "recall", "f1", "specificity", "fpr", "fnr", "roc_auc"]:
        c = ci.get(k)
        lines.append(f"| {k} | {b[k]:.4f} | {f'{c[0]:.4f} - {c[1]:.4f}' if c else 'n/a'} |")
    cm = b["confusion_matrix"]
    lines += ["", f"n = {b['n']}", "", "|  | Pred REAL | Pred AI |", "|---|---|---|",
              f"| **Actual REAL** | TN {cm['TN']} | FP {cm['FP']} |",
              f"| **Actual AI** | FN {cm['FN']} | TP {cm['TP']} |"]
    if "thresholded" in results:
        t = results["thresholded"]
        lines += ["", f"## With uncertainty band (t_low={t['t_low']}, t_high={t['t_high']})", "",
                  f"- Coverage: {t['coverage']:.4f}  (uncertain: {t['uncertain_rate']:.4f}; "
                  f"real {t['uncertain_rate_real']:.4f}, AI {t['uncertain_rate_ai']:.4f})"]
        if "decided" in t:
            d = t["decided"]
            lines.append(f"- On decided images: acc {d['accuracy']:.4f}, P {d['precision']:.4f}, R {d['recall']:.4f}, "
                         f"F1 {d['f1']:.4f}, FPR {d['fpr']:.4f}, FNR {d['fnr']:.4f}")
    if by_results:
        lines += ["", f"## By {by}", "", "| group | n | accuracy | recall | fpr | coverage |", "|---|---|---|---|---|---|"]
        for g, r in by_results.items():
            bb = r["binary@0.5"]
            cov = r.get("thresholded", {}).get("coverage", float("nan"))
            lines.append(f"| {g} | {bb['n']} | {bb['accuracy']:.4f} | {bb['recall']:.4f} | {bb['fpr']:.4f} | {cov:.4f} |")
    return "\n".join(lines) + "\n"


def make_plots(df: pd.DataFrame, results: dict, out_dir: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.metrics import roc_curve

    cm = results["binary@0.5"]["confusion_matrix"]
    mat = np.array([[cm["TN"], cm["FP"]], [cm["FN"], cm["TP"]]])
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.imshow(mat, cmap="Blues")
    for (i, j), v in np.ndenumerate(mat):
        ax.text(j, i, str(v), ha="center", va="center", color="white" if v > mat.max() / 2 else "black")
    ax.set_xticks([0, 1], ["REAL", "AI"]); ax.set_yticks([0, 1], ["REAL", "AI"])
    ax.set_xlabel("Predicted"); ax.set_ylabel("Actual"); ax.set_title("Confusion matrix")
    fig.tight_layout(); fig.savefig(out_dir / "confusion_matrix.png", dpi=150); plt.close(fig)

    if df["label"].nunique() == 2:
        fpr, tpr, _ = roc_curve(df["label"], df["ai_probability"])
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.plot(fpr, tpr, label=f"AUC = {results['binary@0.5']['roc_auc']:.3f}")
        ax.plot([0, 1], [0, 1], "--", color="gray")
        ax.set_xlabel("False positive rate"); ax.set_ylabel("True positive rate"); ax.set_title("ROC"); ax.legend()
        fig.tight_layout(); fig.savefig(out_dir / "roc_curve.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 3.5))
    bins = np.linspace(0, 1, 41)
    ax.hist(df.loc[df["label"] == 0, "ai_probability"], bins=bins, alpha=0.6, label="Actual REAL")
    ax.hist(df.loc[df["label"] == 1, "ai_probability"], bins=bins, alpha=0.6, label="Actual AI")
    t = results.get("thresholded")
    if t:
        for x in (t["t_low"], t["t_high"]):
            ax.axvline(x, color="black", linestyle="--", linewidth=1)
    ax.set_xlabel("AI probability"); ax.set_ylabel("Images"); ax.set_title("Score distribution"); ax.legend()
    fig.tight_layout(); fig.savefig(out_dir / "score_distribution.png", dpi=150); plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("predictions")
    ap.add_argument("--t-low", type=float)
    ap.add_argument("--t-high", type=float)
    ap.add_argument("--by")
    ap.add_argument("--bootstrap", type=int, default=0)
    ap.add_argument("--out-dir")
    ap.add_argument("--plots", action="store_true")
    args = ap.parse_args()

    df = pd.read_csv(args.predictions)
    missing = {"label", "ai_probability"} - set(df.columns)
    if missing:
        raise SystemExit(f"predictions file missing columns: {missing}")
    if not df["ai_probability"].between(0, 1).all():
        raise SystemExit("ai_probability must be in [0, 1]")

    results = evaluate(df, args.t_low, args.t_high, args.bootstrap)
    by_results = None
    if args.by:
        by_results = {str(g): evaluate(sub, args.t_low, args.t_high) for g, sub in df.groupby(args.by)}
        results[f"by_{args.by}"] = by_results

    md = to_markdown(results, by_results, args.by)
    print(md)
    out_dir = Path(args.out_dir) if args.out_dir else Path(args.predictions).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "metrics.json").write_text(json.dumps(results, indent=2))
    (out_dir / "metrics.md").write_text(md, encoding="utf-8")
    if args.plots:
        make_plots(df, results, out_dir)
    print(f"Wrote metrics to {out_dir}")


if __name__ == "__main__":
    main()
