## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.6972 | n/a |
| precision | 0.6495 | n/a |
| recall | 0.6632 | n/a |
| f1 | 0.6562 | n/a |
| specificity | 0.7236 | n/a |
| fpr | 0.2764 | n/a |
| fnr | 0.3368 | n/a |
| roc_auc | 0.7240 | n/a |

n = 218

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 89 | FP 34 |
| **Actual AI** | FN 32 | TP 63 |

## With uncertainty band (t_low=0.1, t_high=0.9)

- Coverage: 0.8532  (uncertain: 0.1468; real 0.1707, AI 0.1158)
- On decided images: acc 0.7312, P 0.7125, R 0.6786, F1 0.6951, FPR 0.2255, FNR 0.3214
