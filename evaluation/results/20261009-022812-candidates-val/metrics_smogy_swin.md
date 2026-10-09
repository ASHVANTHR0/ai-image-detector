## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.8028 | n/a |
| precision | 0.8514 | n/a |
| recall | 0.6632 | n/a |
| f1 | 0.7456 | n/a |
| specificity | 0.9106 | n/a |
| fpr | 0.0894 | n/a |
| fnr | 0.3368 | n/a |
| roc_auc | 0.8718 | n/a |

n = 218

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 112 | FP 11 |
| **Actual AI** | FN 32 | TP 63 |

## With uncertainty band (t_low=0.1, t_high=0.9)

- Coverage: 0.9495  (uncertain: 0.0505; real 0.0244, AI 0.0842)
- On decided images: acc 0.8164, P 0.8451, R 0.6897, F1 0.7595, FPR 0.0917, FNR 0.3103
