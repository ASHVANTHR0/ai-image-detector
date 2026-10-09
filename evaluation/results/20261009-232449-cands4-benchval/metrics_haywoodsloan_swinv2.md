## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.8853 | n/a |
| precision | 0.9605 | n/a |
| recall | 0.7684 | n/a |
| f1 | 0.8538 | n/a |
| specificity | 0.9756 | n/a |
| fpr | 0.0244 | n/a |
| fnr | 0.2316 | n/a |
| roc_auc | 0.9640 | n/a |

n = 218

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 120 | FP 3 |
| **Actual AI** | FN 22 | TP 73 |

## With uncertainty band (t_low=0.3, t_high=0.7)

- Coverage: 0.9908  (uncertain: 0.0092; real 0.0000, AI 0.0211)
- On decided images: acc 0.8889, P 0.9600, R 0.7742, F1 0.8571, FPR 0.0244, FNR 0.2258
