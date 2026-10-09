## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.8333 | n/a |
| precision | 0.8304 | n/a |
| recall | 0.8230 | n/a |
| f1 | 0.8267 | n/a |
| specificity | 0.8430 | n/a |
| fpr | 0.1570 | n/a |
| fnr | 0.1770 | n/a |
| roc_auc | 0.9268 | n/a |

n = 468

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 204 | FP 38 |
| **Actual AI** | FN 40 | TP 186 |

## With uncertainty band (t_low=0.3, t_high=0.7)

- Coverage: 0.6645  (uncertain: 0.3355; real 0.3802, AI 0.2876)
- On decided images: acc 0.9486, P 0.9618, R 0.9379, F1 0.9497, FPR 0.0400, FNR 0.0621
