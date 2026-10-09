## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.8945 | n/a |
| precision | 0.8986 | n/a |
| recall | 0.8158 | n/a |
| f1 | 0.8552 | n/a |
| specificity | 0.9431 | n/a |
| fpr | 0.0569 | n/a |
| fnr | 0.1842 | n/a |
| roc_auc | 0.9537 | n/a |

n = 199

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 116 | FP 7 |
| **Actual AI** | FN 14 | TP 62 |

## With uncertainty band (t_low=0.23, t_high=0.74)

- Coverage: 0.9950  (uncertain: 0.0050; real 0.0081, AI 0.0000)
- On decided images: acc 0.8990, P 0.9118, R 0.8158, F1 0.8611, FPR 0.0492, FNR 0.1842
