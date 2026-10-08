"""Pick the best team of detectors from a candidates run, using VALIDATION predictions only.

    python scripts/evaluate.py --config models/ensemble/candidates.json --manifest dataset/benchmark/manifest.csv \
        --split validation --run-name candidates-val
    python scripts/select_detectors.py evaluation/results/<run_id> [--max-size 4] [--top 7]

Ranks every member by ROC-AUC, then tries every combination of up to --max-size of the --top members. Each member's
scores are first put on a common scale (cross-fitted logistic calibration), then averaged. The team with the best
cross-fitted log-loss (ties: ROC-AUC, then fewer members = faster) is written to models/ensemble/selected.json, ready for
scripts/fit_ensemble.py.
"""
from __future__ import annotations

import argparse
import itertools
import json

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from common import ROOT, resolve


def logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--config", default="models/ensemble/candidates.json")
    ap.add_argument("--max-size", type=int, default=4)
    ap.add_argument("--top", type=int, default=7)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    run = resolve(args.run_dir)
    df = pd.read_csv(run / "predictions.csv")
    if set(df["split"]) - {"validation"}:
        raise SystemExit("Selection must use validation predictions only.")
    config = json.loads(resolve(args.config).read_text())
    y = df["label"].to_numpy().astype(int)
    names = [m["name"] for m in config["members"]]
    cv = StratifiedKFold(5, shuffle=True, random_state=args.seed)

    calibrated, rows = {}, []
    for n in names:
        raw = df[f"score_{n}"].to_numpy()
        calibrated[n] = cross_val_predict(LogisticRegression(C=1e6), logit(raw).reshape(-1, 1), y, cv=cv,
                                          method="predict_proba")[:, 1]
        rows.append({"member": n, "roc_auc": roc_auc_score(y, raw), "acc@0.5": accuracy_score(y, raw >= 0.5),
                     "ai_recall@0.5": (raw[y == 1] >= 0.5).mean(), "real_correct@0.5": (raw[y == 0] < 0.5).mean()})
    ranking = pd.DataFrame(rows).sort_values("roc_auc", ascending=False)
    print("Individual detectors on validation (raw scores, threshold 0.5):")
    print(ranking.round(3).to_string(index=False))

    top = ranking["member"].head(args.top).tolist()
    results = []
    for size in range(1, args.max_size + 1):
        for team in itertools.combinations(top, size):
            p = np.mean([calibrated[n] for n in team], axis=0)
            results.append({"team": team, "size": size, "log_loss": log_loss(y, p), "roc_auc": roc_auc_score(y, p),
                            "acc@0.5": accuracy_score(y, p >= 0.5)})
    teams = pd.DataFrame(results).sort_values(["log_loss", "roc_auc", "size"], ascending=[True, False, True])
    print("\nBest teams (calibrated average, cross-fitted):")
    print(teams.head(10).assign(team=lambda t: t.team.map(" + ".join)).round(4).to_string(index=False))

    best = list(teams.iloc[0]["team"])
    selected = {**config, "version": "selected", "members": [m for m in config["members"] if m["name"] in best]}
    out = ROOT / "models" / "ensemble" / "selected.json"
    out.write_text(json.dumps(selected, indent=2))
    ranking.to_csv(run / "detector_ranking.csv", index=False)
    teams.assign(team=lambda t: t.team.map(" + ".join)).to_csv(run / "team_search.csv", index=False)
    print(f"\nSelected: {' + '.join(best)} -> {out}")


if __name__ == "__main__":
    main()
