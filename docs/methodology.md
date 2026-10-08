# Methodology

Sections marked **TODO** must be filled with the real values once the work is done. Never copy example numbers from the plan.

## Dataset

- **Sources and licenses:** TODO, see `dataset/SOURCES.md`.
- **Layout:** `dataset/raw/real/<source>/`, `dataset/raw/ai/<generator>/`. Labels: 0 = REAL, 1 = AI_GENERATED.
- **Cleaning:** `scripts/dataset_tool.py index` drops files that fail to decode, removes exact duplicates (SHA-256),
  drops identical files that appear under both classes, and groups near-duplicates (64-bit pHash, Hamming distance ≤ 6)
  into a shared `group_id`.
- **Splits:** whole groups are assigned 70/15/15 (train/validation/test), stratified by label, with seed 42. Generators
  passed to `--holdout-generators` go entirely to `test_unseen` for the cross-generator test.
- **Leakage check:** `dataset_tool.py check` fails if any hash or group spans two splits, or if a near-duplicate pair
  crosses a split boundary. It also prints format and resolution per class, to catch shortcuts such as "all AI images are PNG".
- **Counts / class balance / dataset version:** TODO, paste the `check` output.

## Models

- Pretrained detectors: `Organika/sdxl-detector` (Swin, CC BY-NC 3.0) and `umm-maybe/AI-image-detector` (Swin, CC BY 4.0),
  pinned to the revisions in `models/detector_*/source.json`.
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

TODO after Phase 9 (`evaluation/results/final/RESULTS.md`).
