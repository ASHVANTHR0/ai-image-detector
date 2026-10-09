# Final results (Phase 9)

Frozen pipeline: `ensemble-v3b` (see `FREEZE.md`). Evaluated once, on 2026-10-09, on the sealed `test` split of
dataset version `e59e60ea7dea7fb1` (n = 466: 241 real, 225 AI). There is no `test_unseen` split in this dataset
version, so the cross-generator result below comes from the separate OpenFake benchmark run.

## Pipeline

- Members: `haywoodsloan_swinv2` (pretrained Swin-V2), `detector_clip` (frozen CLIP ViT-B/16 + linear head, run
  `20261009-230954-clip_linear`), `detector_clip_ft` (fully fine-tuned CLIP ViT-B/16, run `20261009-231902-clip_vitb16`).
- Combination: logistic regression over the members' log-odds (`logit_stack`), fitted on the validation split.
- Thresholds: `t_low = 0.23`, `t_high = 0.74`, chosen on validation for decided accuracy ≥ 95%, FPR < 5%, FNR < 5%.

## Headline numbers (`test/metrics.md`)

| Metric | Forced decision at 0.5 | 95% CI |
|---|---|---|
| Accuracy | 0.914 | 0.886 – 0.940 |
| Precision | 0.922 | 0.886 – 0.956 |
| Recall | 0.898 | 0.850 – 0.935 |
| F1 | 0.910 | 0.879 – 0.937 |
| FPR | 0.071 | 0.041 – 0.104 |
| FNR | 0.102 | 0.065 – 0.150 |
| ROC-AUC | 0.975 | 0.961 – 0.985 |

With the uncertainty band, 88.4% of images get a decision. On those: accuracy 0.954, precision 0.954, recall 0.949,
F1 0.952, FPR 0.042, FNR 0.051. The remaining 11.6% are returned as `UNCERTAIN`.

## Interpretation

- The project targets (≥ 95% accuracy/P/R/F1, FPR and FNR < 5%) are **met on decided images only**, at the cost of
  abstaining on about 1 in 9 images. Forced to always decide, the system is at about 91%.
- The thresholds were chosen on validation (decided accuracy 0.952, coverage 0.842). The test result is consistent
  with that (0.954, coverage 0.884), so there is no sign the thresholds were overfit.
- Weakest generators on test: FLUX.1-dev (60% recall, n = 20) and FLUX 1.1 Pro (62.5%, n = 8). Several other
  generators have fewer than 5 test images, so their per-generator figures are not reliable.
- Real-photo false positives were the main problem found in error analysis (v2 had 21.5% FPR on validation). On
  test, FPR is 7.1% forced and 4.2% on decided images.

## Cross-generator reference (not a sealed test)

The OpenFake benchmark holdout (`evaluation/results/20261009-023012-ensemble-v1-holdout`, n = 199) uses generators
from OpenFake's *test* split that are absent from our training data. `ensemble-v1` scored 91.0% accuracy there.
`ensemble-v3b` was **not** re-scored on that holdout. It scored 92.2% on the benchmark *validation* split, which it was
not fitted on, but that split was read during model selection.

## Limitations

- **Resolution confound.** Median resolution is 1024×1024 for AI images and 683×683 for real ones. The dataset
  check found no leakage, but the model may partly rely on image size or resampling traces. Models resize inputs to
  224 px, which reduces but does not remove this risk.
- **Small and narrow data.** 3,116 images from one source family (OpenFake: LAION and Pexels reals). The fine-tuned
  CLIP model overfits (99.9% train vs 85.9% validation accuracy).
- **No sealed unseen-generator split** in this dataset version.
- The detector can be fooled by post-processing it was not trained on. Results do not imply universal accuracy.
