## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.9347 | n/a |
| precision | 0.9315 | n/a |
| recall | 0.8947 | n/a |
| f1 | 0.9128 | n/a |
| specificity | 0.9593 | n/a |
| fpr | 0.0407 | n/a |
| fnr | 0.1053 | n/a |
| roc_auc | 0.9712 | n/a |

n = 199

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 118 | FP 5 |
| **Actual AI** | FN 8 | TP 68 |

## With uncertainty band (t_low=0.23, t_high=0.74)

- Coverage: 0.8945  (uncertain: 0.1055; real 0.0650, AI 0.1711)
- On decided images: acc 0.9663, P 0.9672, R 0.9365, F1 0.9516, FPR 0.0174, FNR 0.0635
