## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.8761 | n/a |
| precision | 0.9250 | n/a |
| recall | 0.7789 | n/a |
| f1 | 0.8457 | n/a |
| specificity | 0.9512 | n/a |
| fpr | 0.0488 | n/a |
| fnr | 0.2211 | n/a |
| roc_auc | 0.9388 | n/a |

n = 218

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 117 | FP 6 |
| **Actual AI** | FN 21 | TP 74 |

## With uncertainty band (t_low=0.1, t_high=0.9)

- Coverage: 0.0138  (uncertain: 0.9862; real 1.0000, AI 0.9684)
- On decided images: acc 1.0000, P 1.0000, R 1.0000, F1 1.0000, FPR nan, FNR 0.0000
