## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.7842 | n/a |
| precision | 0.7706 | n/a |
| recall | 0.7876 | n/a |
| f1 | 0.7790 | n/a |
| specificity | 0.7810 | n/a |
| fpr | 0.2190 | n/a |
| fnr | 0.2124 | n/a |
| roc_auc | 0.8525 | n/a |

n = 468

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 189 | FP 53 |
| **Actual AI** | FN 48 | TP 178 |

## With uncertainty band (t_low=0.3, t_high=0.7)

- Coverage: 0.6538  (uncertain: 0.3462; real 0.3554, AI 0.3363)
- On decided images: acc 0.8497, P 0.8662, R 0.8200, F1 0.8425, FPR 0.1218, FNR 0.1800
