## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.8945 | n/a |
| precision | 0.8767 | n/a |
| recall | 0.8421 | n/a |
| f1 | 0.8591 | n/a |
| specificity | 0.9268 | n/a |
| fpr | 0.0732 | n/a |
| fnr | 0.1579 | n/a |
| roc_auc | 0.9311 | n/a |

n = 199

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 114 | FP 9 |
| **Actual AI** | FN 12 | TP 64 |

## With uncertainty band (t_low=0.23, t_high=0.74)

- Coverage: 0.9196  (uncertain: 0.0804; real 0.0813, AI 0.0789)
- On decided images: acc 0.9071, P 0.8955, R 0.8571, F1 0.8759, FPR 0.0619, FNR 0.1429
