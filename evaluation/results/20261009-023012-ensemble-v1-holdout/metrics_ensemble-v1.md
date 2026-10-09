## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.9095 | n/a |
| precision | 0.8816 | n/a |
| recall | 0.8816 | n/a |
| f1 | 0.8816 | n/a |
| specificity | 0.9268 | n/a |
| fpr | 0.0732 | n/a |
| fnr | 0.1184 | n/a |
| roc_auc | 0.9634 | n/a |

n = 199

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 114 | FP 9 |
| **Actual AI** | FN 9 | TP 67 |

## With uncertainty band (t_low=0.39, t_high=0.56)

- Coverage: 0.9849  (uncertain: 0.0151; real 0.0081, AI 0.0263)
- On decided images: acc 0.9184, P 0.8816, R 0.9054, F1 0.8933, FPR 0.0738, FNR 0.0946
