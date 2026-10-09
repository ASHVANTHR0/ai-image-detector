## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.8807 | n/a |
| precision | 0.9259 | n/a |
| recall | 0.7895 | n/a |
| f1 | 0.8523 | n/a |
| specificity | 0.9512 | n/a |
| fpr | 0.0488 | n/a |
| fnr | 0.2105 | n/a |
| roc_auc | 0.9084 | n/a |

n = 218

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 117 | FP 6 |
| **Actual AI** | FN 20 | TP 75 |

## With uncertainty band (t_low=0.3, t_high=0.7)

- Coverage: 0.9771  (uncertain: 0.0229; real 0.0325, AI 0.0105)
- On decided images: acc 0.8826, P 0.9259, R 0.7979, F1 0.8571, FPR 0.0504, FNR 0.2021
