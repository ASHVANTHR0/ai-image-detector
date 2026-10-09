## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.8090 | n/a |
| precision | 0.7317 | n/a |
| recall | 0.7895 | n/a |
| f1 | 0.7595 | n/a |
| specificity | 0.8211 | n/a |
| fpr | 0.1789 | n/a |
| fnr | 0.2105 | n/a |
| roc_auc | 0.8871 | n/a |

n = 199

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 101 | FP 22 |
| **Actual AI** | FN 16 | TP 60 |

## With uncertainty band (t_low=0.39, t_high=0.56)

- Coverage: 1.0000  (uncertain: 0.0000; real 0.0000, AI 0.0000)
- On decided images: acc 0.8090, P 0.7317, R 0.7895, F1 0.7595, FPR 0.1789, FNR 0.2105
