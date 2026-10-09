## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.6055 | n/a |
| precision | 1.0000 | n/a |
| recall | 0.0947 | n/a |
| f1 | 0.1731 | n/a |
| specificity | 1.0000 | n/a |
| fpr | 0.0000 | n/a |
| fnr | 0.9053 | n/a |
| roc_auc | 0.6038 | n/a |

n = 218

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 123 | FP 0 |
| **Actual AI** | FN 86 | TP 9 |

## With uncertainty band (t_low=0.1, t_high=0.9)

- Coverage: 0.9633  (uncertain: 0.0367; real 0.0000, AI 0.0842)
- On decided images: acc 0.5952, P 1.0000, R 0.0230, F1 0.0449, FPR 0.0000, FNR 0.9770
