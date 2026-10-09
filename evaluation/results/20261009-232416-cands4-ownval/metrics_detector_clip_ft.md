## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.8590 | n/a |
| precision | 0.8390 | n/a |
| recall | 0.8761 | n/a |
| f1 | 0.8571 | n/a |
| specificity | 0.8430 | n/a |
| fpr | 0.1570 | n/a |
| fnr | 0.1239 | n/a |
| roc_auc | 0.9396 | n/a |

n = 468

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 204 | FP 38 |
| **Actual AI** | FN 28 | TP 198 |

## With uncertainty band (t_low=0.3, t_high=0.7)

- Coverage: 0.9038  (uncertain: 0.0962; real 0.0992, AI 0.0929)
- On decided images: acc 0.8865, P 0.8685, R 0.9024, F1 0.8852, FPR 0.1284, FNR 0.0976
