## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.7842 | n/a |
| precision | 0.7706 | n/a |
| recall | 0.7876 | n/a |
| f1 | 0.7790 | n/a |
| specificity | 0.7810 | n/a |
| fpr | 0.2190 | n/a |
| fnr | 0.2124 | n/a |
| roc_auc | 0.8525 | n/a |

n = 468

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 189 | FP 53 |
| **Actual AI** | FN 48 | TP 178 |

## With uncertainty band (t_low=0.31, t_high=0.54)

- Coverage: 0.8205  (uncertain: 0.1795; real 0.2273, AI 0.1283)
- On decided images: acc 0.8099, P 0.7897, R 0.8579, F1 0.8224, FPR 0.2406, FNR 0.1421
