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

## With uncertainty band (t_low=0.3, t_high=0.7)

- Coverage: 0.8073  (uncertain: 0.1927; real 0.1626, AI 0.2316)
- On decided images: acc 0.9375, P 0.9697, R 0.8767, F1 0.9209, FPR 0.0194, FNR 0.1233
