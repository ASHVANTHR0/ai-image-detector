## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.4817 | n/a |
| precision | 0.4505 | n/a |
| recall | 0.8632 | n/a |
| f1 | 0.5921 | n/a |
| specificity | 0.1870 | n/a |
| fpr | 0.8130 | n/a |
| fnr | 0.1368 | n/a |
| roc_auc | 0.6614 | n/a |

n = 218

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 23 | FP 100 |
| **Actual AI** | FN 13 | TP 82 |

## With uncertainty band (t_low=0.1, t_high=0.9)

- Coverage: 0.3303  (uncertain: 0.6697; real 0.7886, AI 0.5158)
- On decided images: acc 0.6528, P 0.6479, R 1.0000, F1 0.7863, FPR 0.9615, FNR 0.0000
