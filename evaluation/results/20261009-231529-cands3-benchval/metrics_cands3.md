## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.9541 | n/a |
| precision | 0.9885 | n/a |
| recall | 0.9053 | n/a |
| f1 | 0.9451 | n/a |
| specificity | 0.9919 | n/a |
| fpr | 0.0081 | n/a |
| fnr | 0.0947 | n/a |
| roc_auc | 0.9862 | n/a |

n = 218

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 122 | FP 1 |
| **Actual AI** | FN 9 | TP 86 |

## With uncertainty band (t_low=0.39, t_high=0.56)

- Coverage: 0.9862  (uncertain: 0.0138; real 0.0163, AI 0.0105)
- On decided images: acc 0.9581, P 0.9885, R 0.9149, F1 0.9503, FPR 0.0083, FNR 0.0851
