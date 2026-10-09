## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.6101 | n/a |
| precision | 0.5833 | n/a |
| recall | 0.3684 | n/a |
| f1 | 0.4516 | n/a |
| specificity | 0.7967 | n/a |
| fpr | 0.2033 | n/a |
| fnr | 0.6316 | n/a |
| roc_auc | 0.5913 | n/a |

n = 218

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 98 | FP 25 |
| **Actual AI** | FN 60 | TP 35 |

## With uncertainty band (t_low=0.1, t_high=0.9)

- Coverage: 0.3486  (uncertain: 0.6514; real 0.6585, AI 0.6421)
- On decided images: acc 0.6447, P 0.8889, R 0.2353, F1 0.3721, FPR 0.0238, FNR 0.7647
