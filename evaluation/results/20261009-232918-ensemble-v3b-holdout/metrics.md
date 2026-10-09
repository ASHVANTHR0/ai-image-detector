## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.9347 | 0.8995 - 0.9698 |
| precision | 0.9315 | 0.8718 - 0.9857 |
| recall | 0.8947 | 0.8214 - 0.9565 |
| f1 | 0.9128 | 0.8606 - 0.9578 |
| specificity | 0.9593 | n/a |
| fpr | 0.0407 | 0.0081 - 0.0790 |
| fnr | 0.1053 | 0.0435 - 0.1786 |
| roc_auc | 0.9712 | 0.9439 - 0.9925 |

n = 199

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 118 | FP 5 |
| **Actual AI** | FN 8 | TP 68 |

## With uncertainty band (t_low=0.23, t_high=0.74)

- Coverage: 0.8945  (uncertain: 0.1055; real 0.0650, AI 0.1711)
- On decided images: acc 0.9663, P 0.9672, R 0.9365, F1 0.9516, FPR 0.0174, FNR 0.0635

## By generator

| group | n | accuracy | recall | fpr | coverage |
|---|---|---|---|---|---|
| ernie-image | 1 | 1.0000 | 1.0000 | nan | 1.0000 |
| ernie-image-turbo | 2 | 1.0000 | 1.0000 | nan | 1.0000 |
| flux.2-klein-9b | 7 | 0.8571 | 0.8571 | nan | 0.5714 |
| frames-23-1-25 | 2 | 1.0000 | 1.0000 | nan | 1.0000 |
| gpt-image-1.5 | 7 | 1.0000 | 1.0000 | nan | 1.0000 |
| gpt-image-2 | 1 | 1.0000 | 1.0000 | nan | 1.0000 |
| ideogram-2.0 | 1 | 1.0000 | 1.0000 | nan | 0.0000 |
| illustrious | 7 | 1.0000 | 1.0000 | nan | 1.0000 |
| lumina-17-2-25 | 3 | 1.0000 | 1.0000 | nan | 1.0000 |
| midjourney-7 | 7 | 0.7143 | 0.7143 | nan | 0.8571 |
| nano-banana-pro | 1 | 1.0000 | 1.0000 | nan | 1.0000 |
| none | 123 | 0.9593 | nan | 0.0407 | 0.9350 |
| recraft-v3 | 5 | 0.8000 | 0.8000 | nan | 0.6000 |
| reddit | 7 | 0.5714 | 0.5714 | nan | 0.8571 |
| seedream-v5.0 | 2 | 1.0000 | 1.0000 | nan | 1.0000 |
| sora-2 | 2 | 1.0000 | 1.0000 | nan | 0.5000 |
| veo-3 | 7 | 0.8571 | 0.8571 | nan | 0.8571 |
| wan-video-2.5 | 7 | 1.0000 | 1.0000 | nan | 1.0000 |
| z-image-turbo | 7 | 1.0000 | 1.0000 | nan | 0.5714 |
