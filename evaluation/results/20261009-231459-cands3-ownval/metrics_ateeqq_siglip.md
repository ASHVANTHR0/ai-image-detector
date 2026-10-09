## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.6496 | n/a |
| precision | 0.6099 | n/a |
| recall | 0.7611 | n/a |
| f1 | 0.6772 | n/a |
| specificity | 0.5455 | n/a |
| fpr | 0.4545 | n/a |
| fnr | 0.2389 | n/a |
| roc_auc | 0.7546 | n/a |

n = 468

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 132 | FP 110 |
| **Actual AI** | FN 54 | TP 172 |

## With uncertainty band (t_low=0.39, t_high=0.56)

- Coverage: 0.9957  (uncertain: 0.0043; real 0.0041, AI 0.0044)
- On decided images: acc 0.6524, P 0.6121, R 0.7644, F1 0.6798, FPR 0.4523, FNR 0.2356
