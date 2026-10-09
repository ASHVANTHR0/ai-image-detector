## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.9358 | n/a |
| precision | 0.9880 | n/a |
| recall | 0.8632 | n/a |
| f1 | 0.9213 | n/a |
| specificity | 0.9919 | n/a |
| fpr | 0.0081 | n/a |
| fnr | 0.1368 | n/a |
| roc_auc | 0.9813 | n/a |

n = 218

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 122 | FP 1 |
| **Actual AI** | FN 13 | TP 82 |

## With uncertainty band (t_low=0.3, t_high=0.7)

- Coverage: 0.8211  (uncertain: 0.1789; real 0.1301, AI 0.2421)
- On decided images: acc 0.9665, P 1.0000, R 0.9167, F1 0.9565, FPR 0.0000, FNR 0.0833
