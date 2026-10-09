## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.8995 | n/a |
| precision | 0.8889 | n/a |
| recall | 0.8421 | n/a |
| f1 | 0.8649 | n/a |
| specificity | 0.9350 | n/a |
| fpr | 0.0650 | n/a |
| fnr | 0.1579 | n/a |
| roc_auc | 0.9579 | n/a |

n = 199

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 115 | FP 8 |
| **Actual AI** | FN 12 | TP 64 |

## With uncertainty band (t_low=0.23, t_high=0.74)

- Coverage: 0.7839  (uncertain: 0.2161; real 0.1951, AI 0.2500)
- On decided images: acc 0.9744, P 1.0000, R 0.9298, F1 0.9636, FPR 0.0000, FNR 0.0702
