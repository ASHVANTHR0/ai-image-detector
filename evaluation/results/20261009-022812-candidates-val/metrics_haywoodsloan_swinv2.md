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

## With uncertainty band (t_low=0.1, t_high=0.9)

- Coverage: 0.9633  (uncertain: 0.0367; real 0.0081, AI 0.0737)
- On decided images: acc 0.9143, P 0.9730, R 0.8182, F1 0.8889, FPR 0.0164, FNR 0.1818
