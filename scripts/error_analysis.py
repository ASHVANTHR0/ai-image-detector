"""Error analysis on VALIDATION predictions: outcome per image, error rates per group, contact sheets of the
most confident mistakes, and a report skeleton.

    python scripts/error_analysis.py evaluation/results/<run_id>/predictions.csv

Output: <run_dir>/errors/{outcomes.csv, groups.md, false_positives.png, false_negatives.png, report.md}
"""
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageOps

from common import ENSEMBLE_CONFIG, MANIFEST, resolve

GROUP_COLUMNS = ["generator", "source", "format", "res_bucket", "jpeg_bucket", "mode"]


def describe_image(path: str) -> dict:
    with Image.open(resolve(path)) as im:
        q = None
        if im.format == "JPEG" and getattr(im, "quantization", None):
            q = float(np.mean(im.quantization[0]))
        return {"mode": im.mode, "jpeg_q_table_mean": q}


def res_bucket(w, h) -> str:
    side = max(w, h)
    return "<512" if side < 512 else "512-1024" if side <= 1024 else ">1024"


def jpeg_bucket(q) -> str:
    if q is None or (isinstance(q, float) and np.isnan(q)):
        return "not-jpeg"
    # Lower quantization means higher quality: ~2 at q95, ~10 at q85, ~57 at q50.
    return "high (q>=90)" if q < 5 else "medium" if q < 25 else "low (q<70)"


def contact_sheet(rows: pd.DataFrame, path, title: str, cols: int = 5, tile: int = 220) -> None:
    rows = rows.head(cols * 5)
    if rows.empty:
        return
    n_rows = int(np.ceil(len(rows) / cols))
    sheet = Image.new("RGB", (cols * tile, n_rows * (tile + 30) + 30), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 8), title, fill="black")
    for i, r in enumerate(rows.itertuples()):
        with Image.open(resolve(r.path)) as im:
            thumb = ImageOps.contain(im.convert("RGB"), (tile - 10, tile - 10))
        x, y = (i % cols) * tile, 30 + (i // cols) * (tile + 30)
        sheet.paste(thumb, (x + 5, y + 5))
        draw.text((x + 5, y + tile), f"p_ai={r.ai_probability:.3f} {r.generator}", fill="black")
        draw.text((x + 5, y + tile + 12), str(r.path).split("/")[-1][:34], fill="gray")
    sheet.save(path)


def main() -> None:
    from evaluation.metrics import binary_metrics

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("predictions")
    ap.add_argument("--config", default=str(ENSEMBLE_CONFIG))
    ap.add_argument("--min-group", type=int, default=20, help="groups smaller than this are flagged unreliable")
    args = ap.parse_args()

    pred_path = resolve(args.predictions)
    preds = pd.read_csv(pred_path)
    if preds["split"].isin(["test", "test_unseen"]).any():
        raise SystemExit("Error analysis runs on validation predictions; the test splits stay sealed.")
    config = json.loads(resolve(args.config).read_text())
    t_low, t_high = config["t_low"], config["t_high"]
    if "model" in preds and config["version"] not in set(preds["model"]):
        print(f"WARNING: predictions come from {sorted(set(preds['model']))} but thresholds are from {config['version']}. "
              "Re-run scripts/evaluate.py with the current config so scores and thresholds match.")

    manifest = pd.read_csv(MANIFEST)[["path", "source", "format", "width", "height"]]
    df = preds.merge(manifest, on="path", how="left")
    extra = pd.DataFrame([describe_image(p) for p in df["path"]])
    df = pd.concat([df, extra], axis=1)
    df["res_bucket"] = [res_bucket(w, h) for w, h in zip(df["width"], df["height"])]
    df["jpeg_bucket"] = [jpeg_bucket(q) for q in df["jpeg_q_table_mean"]]

    p, y = df["ai_probability"], df["label"]
    df["outcome@0.5"] = np.select([(p >= .5) & (y == 1), (p < .5) & (y == 0), (p >= .5) & (y == 0)], ["TP", "TN", "FP"], "FN")
    decided = (p >= t_high) | (p <= t_low)
    df["outcome"] = np.where(decided, df["outcome@0.5"], "UNCERTAIN")

    out = pred_path.parent / "errors"
    out.mkdir(exist_ok=True)
    df.to_csv(out / "outcomes.csv", index=False)

    lines = [f"# Error groups ({pred_path.parent.name})", "",
             f"Thresholds t_low={t_low}, t_high={t_high}. Rates use the forced 0.5 decision; "
             f"`uncertain` uses the thresholds. Groups with n < {args.min_group} are marked *.", ""]
    for col in GROUP_COLUMNS:
        lines += [f"## By {col}", "", "| group | n | accuracy | FP rate (real) | FN rate (AI) | uncertain |", "|---|---|---|---|---|---|"]
        for g, sub in df.groupby(col, dropna=False):
            m = binary_metrics(sub["label"], sub["ai_probability"])
            star = "*" if len(sub) < args.min_group else ""
            fmt = lambda v: "n/a" if np.isnan(v) else f"{v:.3f}"
            lines.append(f"| {g}{star} | {len(sub)} | {m['accuracy']:.3f} | {fmt(m['fpr'])} | {fmt(m['fnr'])} | "
                         f"{(sub['outcome'] == 'UNCERTAIN').mean():.3f} |")
        lines.append("")
    score_cols = [c for c in df.columns if c.startswith("score_")]
    if score_cols:
        lines += ["## By ensemble member", "", "| member | accuracy | FPR | FNR | AUC |", "|---|---|---|---|---|"]
        for c in score_cols:
            m = binary_metrics(df["label"], df[c])
            lines.append(f"| {c[6:]} | {m['accuracy']:.3f} | {m['fpr']:.3f} | {m['fnr']:.3f} | {m['roc_auc']:.3f} |")
    (out / "groups.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    fps = df[df["outcome@0.5"] == "FP"].sort_values("ai_probability", ascending=False)
    fns = df[df["outcome@0.5"] == "FN"].sort_values("ai_probability")
    contact_sheet(fps, out / "false_positives.png", "False positives: REAL images scored as AI (most confident first)")
    contact_sheet(fns, out / "false_negatives.png", "False negatives: AI images scored as REAL (most confident first)")

    counts = df["outcome"].value_counts().to_dict()
    report = out / "report.md"
    if not report.exists():
        report.write_text(
            f"# Error analysis report - {pred_path.parent.name}\n\nOutcomes (with thresholds): {counts}\n\n"
            "See groups.md and the contact sheets.\n\n## Findings\n\n| Error group | Evidence | Hypothesis | Fix |\n"
            "|---|---|---|---|\n|  |  |  |  |\n\n## Changes made and before/after validation metrics\n\n",
            encoding="utf-8")
    print(f"Outcomes: {counts}")
    print(f"FP {len(fps)}, FN {len(fns)} at 0.5. Wrote {out}")


if __name__ == "__main__":
    main()
