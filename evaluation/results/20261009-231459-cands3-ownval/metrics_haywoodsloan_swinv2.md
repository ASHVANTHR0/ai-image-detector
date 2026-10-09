## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.8355 | n/a |
| precision | 0.8901 | n/a |
| recall | 0.7522 | n/a |
| f1 | 0.8153 | n/a |
| specificity | 0.9132 | n/a |
| fpr | 0.0868 | n/a |
| fnr | 0.2478 | n/a |
| roc_auc | 0.8866 | n/a |

n = 468

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 221 | FP 21 |
| **Actual AI** | FN 56 | TP 170 |

## With uncertainty band (t_low=0.39, t_high=0.56)

- Coverage: 1.0000  (uncertain: 0.0000; real 0.0000, AI 0.0000)
- On decided images: acc 0.8355, P 0.8901, R 0.7522, F1 0.8153, FPR 0.0868, FNR 0.2478
