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
| roc_auc | 0.9346 | n/a |

n = 218

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 117 | FP 6 |
| **Actual AI** | FN 21 | TP 74 |

## With uncertainty band (t_low=0.39, t_high=0.56)

- Coverage: 0.8716  (uncertain: 0.1284; real 0.1220, AI 0.1368)
- On decided images: acc 0.9158, P 0.9583, R 0.8415, F1 0.8961, FPR 0.0278, FNR 0.1585
