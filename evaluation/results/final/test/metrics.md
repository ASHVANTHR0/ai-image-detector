## Overall (forced binary, threshold 0.5)

| Metric | Value | 95% CI |
|---|---|---|
| accuracy | 0.9142 | 0.8863 - 0.9399 |
| precision | 0.9224 | 0.8858 - 0.9556 |
| recall | 0.8978 | 0.8496 - 0.9351 |
| f1 | 0.9099 | 0.8785 - 0.9369 |
| specificity | 0.9295 | n/a |
| fpr | 0.0705 | 0.0405 - 0.1040 |
| fnr | 0.1022 | 0.0649 - 0.1504 |
| roc_auc | 0.9746 | 0.9613 - 0.9854 |

n = 466

|  | Pred REAL | Pred AI |
|---|---|---|
| **Actual REAL** | TN 224 | FP 17 |
| **Actual AI** | FN 23 | TP 202 |

## With uncertainty band (t_low=0.23, t_high=0.74)

- Coverage: 0.8841  (uncertain: 0.1159; real 0.1079, AI 0.1244)
- On decided images: acc 0.9539, P 0.9541, R 0.9492, F1 0.9517, FPR 0.0419, FNR 0.0508

## By generator

| group | n | accuracy | recall | fpr | coverage |
|---|---|---|---|---|---|
| none | 241 | 0.9295 | nan | 0.0705 | 0.8921 |
| openfake-amateur-photography-v6 | 1 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-anima-preview | 1 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-animagine-xl-4.0 | 1 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-chroma | 1 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-cyberrealistic-pony-v14.1 | 3 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-cyberrealistic-pony-v15.0 | 2 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-cyberrealistic-pony-v17.0 | 1 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-cyberrealistic-xl-v9.0 | 1 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-dalle-3 | 4 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-flux-1.1-pro | 8 | 0.6250 | 0.6250 | nan | 0.5000 |
| openfake-flux-amateursnapshotphotos | 1 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-flux-mvc5000 | 1 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-flux-realism | 1 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-flux.1-dev | 20 | 0.6000 | 0.6000 | nan | 0.7000 |
| openfake-flux.1-schnell | 11 | 0.9091 | 0.9091 | nan | 1.0000 |
| openfake-flux.2-dev | 2 | 0.5000 | 0.5000 | nan | 0.5000 |
| openfake-flux.2-klein-base-4b | 1 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-gpt-image-1 | 14 | 1.0000 | 1.0000 | nan | 0.9286 |
| openfake-grok-2-image-1212 | 1 | 1.0000 | 1.0000 | nan | 0.0000 |
| openfake-hidream-i1-full | 4 | 1.0000 | 1.0000 | nan | 0.7500 |
| openfake-hunyuan-video | 1 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-ideogram-3.0 | 7 | 0.8571 | 0.8571 | nan | 1.0000 |
| openfake-imagen-3.0-002 | 2 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-imagen-4.0 | 3 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-kolors-v1.0 | 1 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-midjourney-6 | 4 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-mystic | 3 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-openflux.1 | 1 | 0.0000 | 0.0000 | nan | 0.0000 |
| openfake-playground-v2.5-1024px-aesthetic | 2 | 1.0000 | 1.0000 | nan | 0.5000 |
| openfake-qwen-image | 1 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-realistic_vision_v5.1_novae | 2 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-sd-1.5 | 4 | 1.0000 | 1.0000 | nan | 0.7500 |
| openfake-sd-1.5-dreamshaper | 12 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-sd-1.5-epicdream | 3 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-sd-2.1 | 21 | 0.9048 | 0.9048 | nan | 0.7619 |
| openfake-sd-3.5 | 29 | 0.8621 | 0.8621 | nan | 0.8276 |
| openfake-sd-turbo | 3 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-sd-xl-v1.0-vae-fix | 1 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-sdxl | 8 | 1.0000 | 1.0000 | nan | 0.8750 |
| openfake-sdxl-1.0 | 1 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-sdxl-epic-realism | 10 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-sdxl-juggernaut | 6 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-sdxl-realvis-v5 | 4 | 0.7500 | 0.7500 | nan | 1.0000 |
| openfake-sdxl-touchofrealism | 5 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-sdxl-turbo | 2 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-seedream-v4.5 | 1 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-stable-diffusion-v1-4 | 1 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-stable-diffusion-v1-5 | 2 | 0.5000 | 0.5000 | nan | 1.0000 |
| openfake-studio-ghibli-wan2.1-t2v-14b-v1.0 | 2 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-tiny-random-sana | 1 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-wan-video-2.1 | 1 | 1.0000 | 1.0000 | nan | 1.0000 |
| openfake-wan-video-2.2 | 2 | 1.0000 | 1.0000 | nan | 1.0000 |
