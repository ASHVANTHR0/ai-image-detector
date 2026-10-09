## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.9095 | 0.8693 - 0.9497 |
| precision | 0.8816 | 0.8028 - 0.9481 |
| recall | 0.8816 | 0.8030 - 0.9481 |
| f1 | 0.8816 | 0.8197 - 0.9342 |
| specificity | 0.9268 | n/a |
| fpr | 0.0732 | 0.0308 - 0.1231 |
| fnr | 0.1184 | 0.0519 - 0.1970 |
| roc_auc | 0.9634 | 0.9328 - 0.9872 |

n = 199

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 114 | FP 9 |
| **Actual AI** | FN 9 | TP 67 |

## With uncertainty band (t_low=0.39, t_high=0.56)

- Coverage: 0.9849  (uncertain: 0.0151; real 0.0081, AI 0.0263)
- On decided images: acc 0.9184, P 0.8816, R 0.9054, F1 0.8933, FPR 0.0738, FNR 0.0946

## By generator

| group | n | accuracy | recall | fpr | coverage |
|---|---|---|---|---|---|
| ernie-image | 1 | 1.0000 | 1.0000 | nan | 1.0000 |
| ernie-image-turbo | 2 | 1.0000 | 1.0000 | nan | 1.0000 |
| flux.2-klein-9b | 7 | 0.4286 | 0.4286 | nan | 0.8571 |
| frames-23-1-25 | 2 | 1.0000 | 1.0000 | nan | 1.0000 |
| gpt-image-1.5 | 7 | 1.0000 | 1.0000 | nan | 1.0000 |
| gpt-image-2 | 1 | 1.0000 | 1.0000 | nan | 1.0000 |
| ideogram-2.0 | 1 | 1.0000 | 1.0000 | nan | 1.0000 |
| illustrious | 7 | 1.0000 | 1.0000 | nan | 1.0000 |
| lumina-17-2-25 | 3 | 1.0000 | 1.0000 | nan | 1.0000 |
| midjourney-7 | 7 | 0.8571 | 0.8571 | nan | 1.0000 |
| nano-banana-pro | 1 | 1.0000 | 1.0000 | nan | 1.0000 |
| none | 123 | 0.9268 | nan | 0.0732 | 0.9919 |
| recraft-v3 | 5 | 1.0000 | 1.0000 | nan | 1.0000 |
| reddit | 7 | 0.7143 | 0.7143 | nan | 1.0000 |
| seedream-v5.0 | 2 | 1.0000 | 1.0000 | nan | 1.0000 |
| sora-2 | 2 | 1.0000 | 1.0000 | nan | 1.0000 |
| veo-3 | 7 | 1.0000 | 1.0000 | nan | 1.0000 |
| wan-video-2.5 | 7 | 1.0000 | 1.0000 | nan | 1.0000 |
| z-image-turbo | 7 | 0.7143 | 0.7143 | nan | 0.8571 |
