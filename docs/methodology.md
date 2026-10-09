# Methodology

## Dataset

- **Sources and licenses:** OpenFake (`ComplexDataLab/OpenFake`, CC BY-NC 4.0), *train* split only, fetched with
  `scripts/fetch_training_data.py`. Reals come from LAION and Pexels; AI images come from 60+ generators. All images are
  re-encoded the same way (RGB, max side 1024, JPEG q95), and images whose SHA-256 appears in the benchmark manifest
  are skipped. See `dataset/SOURCES.md`.
- **Layout:** `dataset/raw/real/<source>/`, `dataset/raw/ai/<generator>/`. Labels: 0 = REAL, 1 = AI_GENERATED.
- **Cleaning:** `scripts/dataset_tool.py index` drops files that fail to decode, removes exact duplicates (SHA-256),
  drops identical files that appear under both classes, and groups near-duplicates (64-bit pHash, Hamming distance ≤ 6)
  into a shared `group_id`.
- **Splits:** whole groups are assigned 70/15/15 (train/validation/test), stratified by label, with seed 42. Generators
  passed to `--holdout-generators` go entirely to `test_unseen` for the cross-generator test.
- **Leakage check:** `dataset_tool.py check` fails if any hash or group spans two splits, or if a near-duplicate pair
  crosses a split boundary. It also prints format and resolution per class, to catch shortcuts such as "all AI images are PNG".
- **Counts / class balance / dataset version:** 3,116 images (1,612 REAL, 1,504 AI_GENERATED), all JPEG. Splits:
  train 2,182 / validation 468 / test 466; no `test_unseen`. Median resolution is 1024×1024 for AI and 683×683 for
  real (a possible size shortcut, see Limitations). Dataset version `e59e60ea7dea7fb1`. `check` reports no leakage.

## Models

- Pretrained detectors: nine Hugging Face candidates were scored on the OpenFake benchmark validation split
  (`evaluation/results/20261009-022812-candidates-val`). `haywoodsloan_swinv2` was the strongest and is kept in the
  final ensemble.
- Custom detectors (final): `detector_clip`, a frozen CLIP ViT-B/16 with a trained linear head (validation AUC 0.853),
  and `detector_clip_ft`, a fully fine-tuned CLIP ViT-B/16 (validation AUC 0.940). See `docs/experiments.md`.
- Custom detector: transfer learning with `scripts/train.py`. A pretrained timm backbone (default ConvNeXt-Tiny;
  CLIP ViT-B/16 config provided) gets a single-logit head. Stage 1 trains only the head, with the backbone and its
  BatchNorm statistics frozen. Stage 2 fine-tunes everything with AdamW, warmup + cosine schedule, mixed precision,
  and early stopping on validation ROC-AUC.
- Augmentation (training only): random JPEG re-compression (quality 60–100, applied to both classes), mild blur,
  random resized crop (scale 0.6–1), horizontal flip, ±10° rotation, brightness/contrast jitter.

## Ensemble and uncertainty

`scripts/fit_ensemble.py` compares each member, the mean, a weighted average (grid search on validation ROC-AUC, ties
broken by log-loss), majority voting and cross-validated stacking. It fits Platt calibration with cross-fitting, then
searches `t_low`/`t_high` for the widest coverage that keeps decided accuracy ≥ 95%, FPR < 5% and FNR < 5%. The
risk–coverage curve answers RQ5.

## Evaluation protocol

1. All tuning (hyperparameters, weights, thresholds, model choice) uses the validation split only. The scripts refuse
   to read `test`/`test_unseen`.
2. `scripts/final_evaluation.py --confirm` records a freeze (git commit, config and weight hashes, dataset version,
   pre-registered metrics), then evaluates once on `test` (seen generators) and `test_unseen` (unseen generators).
3. Reported metrics: accuracy, precision, recall, F1, specificity, FPR, FNR, ROC-AUC with 95% bootstrap CIs, the
   confusion matrix, coverage and uncertain rate, per-generator accuracy, and inference time.
4. All numbers come from `evaluation/metrics.py` and can be regenerated from the saved `predictions.csv` files.

## Results

Final pipeline `ensemble-v3b` (swinv2 + both CLIP detectors, logit stacking fitted on validation, t_low 0.23 /
t_high 0.74). Results on the sealed test split (n = 466), with 95% bootstrap CIs: accuracy 0.914 (0.886–0.940),
F1 0.910, FPR 0.071, FNR 0.102, ROC-AUC 0.975 (0.961–0.985). On the 88.4% of images it decides: accuracy 0.954,
FPR 0.042, FNR 0.051. Full results and limitations: `evaluation/results/final/RESULTS.md`.
