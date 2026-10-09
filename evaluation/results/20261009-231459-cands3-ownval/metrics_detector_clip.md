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

## With uncertainty band (t_low=0.39, t_high=0.56)

- Coverage: 0.8697  (uncertain: 0.1303; real 0.1446, AI 0.1150)
- On decided images: acc 0.8133, P 0.7952, R 0.8350, F1 0.8146, FPR 0.2077, FNR 0.1650
