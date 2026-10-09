## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.6651 | n/a |
| precision | 0.6250 | n/a |
| recall | 0.5789 | n/a |
| f1 | 0.6011 | n/a |
| specificity | 0.7317 | n/a |
| fpr | 0.2683 | n/a |
| fnr | 0.4211 | n/a |
| roc_auc | 0.6979 | n/a |

n = 218

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 90 | FP 33 |
| **Actual AI** | FN 40 | TP 55 |

## With uncertainty band (t_low=0.1, t_high=0.9)

- Coverage: 0.8303  (uncertain: 0.1697; real 0.1870, AI 0.1474)
- On decided images: acc 0.6851, P 0.6622, R 0.6049, F1 0.6323, FPR 0.2500, FNR 0.3951
