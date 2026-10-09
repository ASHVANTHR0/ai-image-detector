## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.8184 | n/a |
| precision | 0.7878 | n/a |
| recall | 0.8540 | n/a |
| f1 | 0.8195 | n/a |
| specificity | 0.7851 | n/a |
| fpr | 0.2149 | n/a |
| fnr | 0.1460 | n/a |
| roc_auc | 0.9156 | n/a |

n = 468

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 190 | FP 52 |
| **Actual AI** | FN 33 | TP 193 |

## With uncertainty band (t_low=0.31, t_high=0.54)

- Coverage: 0.9209  (uncertain: 0.0791; real 0.0992, AI 0.0575)
- On decided images: acc 0.8376, P 0.7967, R 0.9014, F1 0.8458, FPR 0.2248, FNR 0.0986
