## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.8211 | n/a |
| precision | 0.7917 | n/a |
| recall | 0.8000 | n/a |
| f1 | 0.7958 | n/a |
| specificity | 0.8374 | n/a |
| fpr | 0.1626 | n/a |
| fnr | 0.2000 | n/a |
| roc_auc | 0.9089 | n/a |

n = 218

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 103 | FP 20 |
| **Actual AI** | FN 19 | TP 76 |

## With uncertainty band (t_low=0.1, t_high=0.9)

- Coverage: 0.9725  (uncertain: 0.0275; real 0.0325, AI 0.0211)
- On decided images: acc 0.8396, P 0.8172, R 0.8172, F1 0.8172, FPR 0.1429, FNR 0.1828
