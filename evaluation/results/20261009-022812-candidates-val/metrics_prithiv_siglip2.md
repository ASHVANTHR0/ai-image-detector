## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.4587 | n/a |
| precision | 0.4460 | n/a |
| recall | 1.0000 | n/a |
| f1 | 0.6169 | n/a |
| specificity | 0.0407 | n/a |
| fpr | 0.9593 | n/a |
| fnr | 0.0000 | n/a |
| roc_auc | 0.6941 | n/a |

n = 218

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 5 | FP 118 |
| **Actual AI** | FN 0 | TP 95 |

## With uncertainty band (t_low=0.1, t_high=0.9)

- Coverage: 0.9908  (uncertain: 0.0092; real 0.0163, AI 0.0000)
- On decided images: acc 0.4583, P 0.4481, R 1.0000, F1 0.6189, FPR 0.9669, FNR 0.0000
