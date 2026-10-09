## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.8141 | n/a |
| precision | 0.7837 | n/a |
| recall | 0.8496 | n/a |
| f1 | 0.8153 | n/a |
| specificity | 0.7810 | n/a |
| fpr | 0.2190 | n/a |
| fnr | 0.1504 | n/a |
| roc_auc | 0.9060 | n/a |

n = 468

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 189 | FP 53 |
| **Actual AI** | FN 34 | TP 192 |

## With uncertainty band (t_low=0.39, t_high=0.56)

- Coverage: 0.9487  (uncertain: 0.0513; real 0.0744, AI 0.0265)
- On decided images: acc 0.8266, P 0.8043, R 0.8591, F1 0.8308, FPR 0.2054, FNR 0.1409
