# AI-Generated Image Detection and Authenticity Verification Using Deep Learning

*Final project report. Every number here comes from a file in this repository; the source is given next to each table.*

---

## Abstract

Image generators such as FLUX, Midjourney, Stable Diffusion and GPT Image now produce pictures that people cannot
reliably tell apart from photographs. This project builds a completely free, locally deployable system that classifies
an uploaded image as **AI-generated**, **real**, or **uncertain**. Pretrained open-source detectors were benchmarked,
two detectors were trained by transfer learning from CLIP ViT-B/16, and three models were combined with a logistic
stacking ensemble whose two decision thresholds create an explicit *uncertain* band. A C2PA / metadata provenance
check runs before the detectors. The application is a FastAPI backend with SQLite storage and a Vue 3 dashboard, and
runs offline after the models are downloaded.

On a sealed, leakage-checked test set of 466 OpenFake images (241 real, 225 AI, 60+ generators), the frozen ensemble
reached **91.4% accuracy (95% CI 88.6–94.0%) and ROC-AUC 0.975** when forced to decide. It abstained on 11.6% of images.
On the rest it was **95.4% accurate, with a 4.2% false-positive rate**. On a separate benchmark of 199 images whose
AI images come from generators never seen in training (GPT Image 1.5/2, Midjourney 7, Sora 2, Veo 3, FLUX.2 and
others), it reached **93.5% accuracy (CI 90.0–97.0%)**. Heavy JPEG compression is the main weakness: at quality 30 the
share of AI images missed rises from 9.7% to 44.7%. These results hold for the data described here. They do not show
universal accuracy.

---

## 1. Introduction

Diffusion and autoregressive image models have made photorealistic synthetic images cheap. Such images are used in
misinformation, fraud and fake profiles. At the same time, false accusations of "AI" against genuine photographs
cause their own harm. A useful detector must therefore report its confidence, abstain when it does not know, and be
evaluated honestly on images and generators it has not seen.

Commercial services exist, but they are paid, closed and network-dependent. This project shows that a competitive
detector can be built and evaluated with free tools on a consumer laptop (RTX 4050, 6 GB).

## 2. Problem statement

Given a single image, estimate the probability that it was produced by a generative model, and return a decision
(AI-generated / real / uncertain) with a confidence level. Do this locally, at no cost, with measured and
reproducible performance, including on generators absent from the training data.

## 3. Objectives

> **To design and implement a completely free, locally deployable AI-generated image detection system using open-source
> deep-learning models, capable of classifying images as AI-generated, real, or uncertain, while evaluating model
> performance across diverse datasets and multiple image-generation sources.**

Specific objectives:
1. Build a leakage-free dataset with group-aware splits.
2. Benchmark pretrained open-source detectors.
3. Train custom detectors by transfer learning.
4. Combine detectors in an ensemble with calibrated uncertainty thresholds.
5. Analyse errors and improve the system before the final test.
6. Evaluate once on a sealed test set and on unseen generators.
7. Deliver a usable web application with history and analytics.

Targets for the controlled test set: accuracy, precision, recall and F1 ≥ 95%, with FPR and FNR < 5%.

## 4. Literature review

**GAN-era detectors.** Wang et al. [1] showed that a ResNet-50 trained on images from a single GAN (ProGAN), with
blur and JPEG augmentation, generalizes surprisingly well to other CNN generators. Their result established
augmentation with compression as standard practice, which this project follows.

**Diffusion models.** Corvi et al. [2] found that diffusion models leave their own forensic traces, that detectors
built for GANs transfer poorly to them, and that compression and resizing on social networks degrade detection
sharply. Our robustness experiment (§12.5) reproduces this compression effect.

**Foundation-model features.** Ojha, Li and Lee [3] ("UnivFD") showed that a *frozen* CLIP ViT [4] with a linear
classifier generalizes to unseen generators much better than a fully trained network, because the backbone cannot
overfit to the training generators' artifacts. Our `detector_clip` follows this design; `detector_clip_ft` tests the
opposite choice of full fine-tuning.

**Backbones.** Vision Transformers [5], Swin Transformer V2 [6] and SigLIP [7] are the architectures behind the
pretrained detectors evaluated here.

**Datasets.** GenImage [8] provides a million-scale benchmark across eight generators. OpenFake [9] (2025) provides
about 3 million real images and almost 1 million synthetic images from modern proprietary and open generators. Its train
and test splits use different generators, which makes it suitable for cross-generator evaluation. We use it for both
training data and the unseen-generator benchmark.

**Ensembles and selective classification.** Stacked generalization [10] learns how to combine member predictions,
and Platt scaling [11] turns scores into calibrated probabilities. Selective classification [12] lets a model abstain
on low-confidence inputs to reduce risk on the inputs it does decide. Our UNCERTAIN band applies this idea.

**Provenance.** The C2PA specification [13] defines cryptographically signed Content Credentials that state how a
file was made. It is reliable when present but easy to strip, so it can only *confirm* AI origin, never rule it out.

## 5. Existing systems

Commercial detectors such as *AI or Not* offer an API. They were not used as the core of this project (plan §5):
- they have usage limits and possible pricing changes;
- they need a network connection and depend on an outside service;
- their models are not open, so results cannot be reproduced or explained.

Open-source detectors on Hugging Face are free, but their quality varies widely and they are rarely evaluated on
recent generators (§12.1). Many are trained on a few generators and fail on newer ones.

## 6. Proposed system

A local web application:
1. a **provenance validator** (C2PA, IPTC DigitalSourceType, embedded generation parameters);
2. an **ensemble of three detectors**, combined by logistic stacking over their log-odds;
3. a **three-way decision** with two thresholds (`t_low`, `t_high`);
4. **forensic indicators** (EXIF, software tag, JPEG quality, noise, FFT ratio), shown to the user but never used for
   the decision;
5. a **dashboard** with detection history and analytics.

## 7. Requirements

**Functional.** Upload an image; validate the file; preprocess; run local detectors; optionally extract forensic
features; combine detector outputs; return AI and real probabilities, prediction, confidence, processing time and
model version; store the result; show history and statistics; work without an external API.

**Non-functional.** Free software only; local-first; no cloud dependency; reproducible experiments; secure file
validation; clear uncertainty handling; strict train/validation/test separation; documented methodology.

## 8. Architecture

```
Browser (Vue 3 + Tailwind + Chart.js)
   │  /api/* (Vite proxy)
   ▼
FastAPI :8765 ── loads the ensemble once at startup
   ├─ POST /api/v1/detect        validate → hash → cache? → preprocess → provenance → ensemble → forensics → store
   ├─ GET  /api/v1/detections    history (paginated, filterable)
   ├─ GET  /api/v1/detections/{id}
   ├─ GET  /api/v1/statistics    counts, histograms, model version metrics
   ├─ GET  /api/v1/evaluation    final-test results (summary.json)
   └─ GET  /api/v1/health
        └─ SQLite (SQLAlchemy): detections, model_versions
```

Uploaded images are never written to disk. Only the result and the file's SHA-256 are stored. Full details:
`docs/architecture.md`.

## 9. Methodology

1. **Dataset (Phase 2).** Collect, normalize, deduplicate and split by group (§10).
2. **Baseline (Phase 3).** Score nine pretrained Hugging Face detectors on a validation split.
3. **Training (Phase 4).** Train two CLIP ViT-B/16 detectors by transfer learning.
4. **Ensemble (Phase 5).** Fit stacking weights and thresholds on validation.
5. **Error analysis (Phase 6).** Find and fix the dominant failure mode before freezing.
6. **Final evaluation (Phase 9).** Freeze, record hashes, evaluate once on the test set, then evaluate once on the
   unseen-generator benchmark.

**Integrity rules.** Every tuning decision used validation data only. The scripts refuse to read the `test` split
unless called from `final_evaluation.py --confirm`. Seeds are fixed at 42. Result files are never edited by hand.

## 10. Dataset

**Source.** OpenFake [9] (`ComplexDataLab/OpenFake`, CC BY-NC 4.0), *train* split. Real images come from LAION and
Pexels; AI images come from 60+ generators (FLUX.1, SD 1.5/2.1/3.5, SDXL variants, DALL·E 3, Midjourney 6,
GPT Image 1, Imagen 4, Ideogram 3, HiDream and others).

**Normalization.** Every image, of either class, is converted to RGB, downscaled to at most 1024 px and saved as JPEG
quality 95. This removes the shortcut where "PNG means AI".

**Deduplication and leakage control.** Exact duplicates are removed by SHA-256. Near-duplicates (64-bit perceptual
hash, Hamming distance ≤ 6) share a `group_id`, and a group never spans splits. Images whose hash appears in the
benchmark were excluded. `dataset_tool.py check` reports **no leakage**.

| Split | Images |
|---|---|
| train | 2,182 |
| validation | 468 |
| test | 466 |
| **total** | **3,116** (1,612 real, 1,504 AI) |

Dataset version (manifest SHA-256 prefix): `e59e60ea7dea7fb1`.

**Unseen-generator benchmark.** 417 images from OpenFake's *test* split: real photos plus generators absent from
its train split (`dataset/benchmark/manifest.csv`). It is split into validation (218) and holdout (199).

**Known bias.** Median resolution is 1024 × 1024 for AI images and 683 × 683 for real images. The models resize
inputs to 224 px, but resampling traces could still act as a shortcut (§14).

## 11. Models

| Member | Type | Source | Role |
|---|---|---|---|
| `haywoodsloan_swinv2` | Swin-V2 classifier [6] | `haywoodsloan/ai-image-detector-deploy` (Apache-2.0), pinned revision | best pretrained detector |
| `detector_clip` | frozen CLIP ViT-B/16 + linear head [3] | trained here, run `20261009-230954-clip_linear` | generalization |
| `detector_clip_ft` | CLIP ViT-B/16, fully fine-tuned | trained here, run `20261009-231902-clip_vitb16` | in-distribution accuracy |

**Training.** Both detectors use a timm backbone with a single-logit head trained with `BCEWithLogits`.
- *Stage 1:* train only the head (lr 1e-3).
- *Stage 2 (`detector_clip_ft` only):* fine-tune the whole network with AdamW (lr 2e-5, weight decay 0.05), one warmup
  epoch, a cosine schedule, mixed precision, and early stopping on validation ROC-AUC.
- *Augmentation (training only):* random JPEG re-compression (quality 60–100, both classes), blur, random resized
  crop (scale 0.6–1), flip, ±10° rotation, brightness/contrast jitter.

| Run | Validation accuracy | F1 | ROC-AUC | Training time |
|---|---|---|---|---|
| clip_linear (15 head epochs) | 0.786 | 0.781 | 0.853 | ≈ 3.5 min |
| clip_vitb16 (3 head + 8 full epochs) | 0.859 | 0.857 | 0.940 | ≈ 4 min |

Source: `docs/experiments.md`, `experiments/*/metrics.json`.

**Ensemble.** `logit_stack`: p = σ(b + Σ wᵢ · logit(sᵢ)), with weights fitted by logistic regression on validation.
Coefficients: swinv2 0.250, clip 0.113, clip_ft 0.462, intercept 0.114. The thresholds were chosen for the widest
coverage that keeps decided accuracy ≥ 95% and FPR, FNR < 5% on validation: `t_low = 0.23`, `t_high = 0.74`.
Confidence is HIGH if decided and max(p, 1−p) ≥ 0.9, MEDIUM if decided otherwise, and LOW if uncertain.

## 12. Results

### 12.1 Baseline: pretrained detectors

Nine Hugging Face detectors were scored on the benchmark validation split (n = 218).
Source: `evaluation/results/20261009-022812-candidates-val/detector_ranking.csv`.

| Detector | ROC-AUC | Accuracy @0.5 |
|---|---|---|
| haywoodsloan_swinv2 | 0.964 | 0.885 |
| ateeqq_siglip | 0.909 | 0.821 |
| smogy_swin | 0.872 | 0.803 |
| sdxl_detector (Organika) | 0.724 | 0.697 |
| nyuad_vit | 0.698 | 0.665 |
| prithiv_siglip2 | 0.694 | 0.459 |
| dima806_vit_real | 0.661 | 0.482 |
| dima806_vit_human | 0.604 | 0.606 |
| ai_image_detector (umm-maybe) | 0.591 | 0.610 |

Most public detectors are close to chance on modern generators, and only two exceed AUC 0.9.

### 12.2 Error analysis and improvement (Phase 6)

The intermediate `ensemble-v2` (siglip + swinv2 + clip probe, fitted on the benchmark) reached 95.4% on benchmark
validation. On our own validation split, however, it flagged **21.5% of real photos as AI** (28.7% of LAION, 14.2% of
Pexels). Source: `evaluation/results/20261009-231701-ensemble-v2-ownval/errors/`.

Fixes applied before freezing:
- trained the fully fine-tuned `detector_clip_ft`;
- refitted the stack on our own validation split;
- dropped siglip, which had a negative weight.

On validation, cross-fitted FPR fell from 21.5% to 9.5%. With the uncertainty band, decided accuracy was 95.2% at 84%
coverage.

### 12.3 Final test: seen generators (sealed, run once)

Source: `evaluation/results/final/test/metrics.md`, freeze record `FREEZE.md`. n = 466.

| Metric | Forced decision (0.5) | 95% bootstrap CI |
|---|---|---|
| Accuracy | **0.914** | 0.886 – 0.940 |
| Precision | 0.922 | 0.886 – 0.956 |
| Recall | 0.898 | 0.850 – 0.935 |
| F1 | 0.910 | 0.879 – 0.937 |
| Specificity | 0.930 | — |
| FPR | 0.071 | 0.041 – 0.104 |
| FNR | 0.102 | 0.065 – 0.150 |
| ROC-AUC | **0.975** | 0.961 – 0.985 |

Confusion matrix: TN 224, FP 17, FN 23, TP 202 (see `confusion_matrix.png`, `roc_curve.png`).

**With the uncertainty band:** 88.4% of images are decided. On those, accuracy is 0.954, precision 0.954, recall
0.949, F1 0.952, FPR 0.042 and FNR 0.051.

Weakest generators on test: FLUX.1-dev (60% recall, n = 20) and FLUX 1.1 Pro (62.5%, n = 8). Most generators have
fewer than 10 test images, so per-generator figures are indicative only.

Mean inference time: 52 ms per image for the three members on an RTX 4050.

### 12.4 Cross-generator test: unseen generators

The frozen `ensemble-v3b` was run once on the benchmark holdout (n = 199). Its AI images come from OpenFake test
generators that do not appear in our training data. Source: `evaluation/results/20261009-232918-ensemble-v3b-holdout/`.

| Metric | Forced (0.5) | 95% CI |
|---|---|---|
| Accuracy | **0.935** | 0.900 – 0.970 |
| F1 | 0.913 | 0.861 – 0.958 |
| FPR | 0.041 | 0.008 – 0.079 |
| FNR | 0.105 | 0.044 – 0.179 |
| ROC-AUC | 0.971 | 0.944 – 0.993 |

With the band, coverage is 89.5%. On decided images, accuracy is 0.966 and FPR 0.017. The earlier `ensemble-v1`
scored 0.910 on the same holdout. Weak generators include Midjourney 7 (5 of 7 caught), images scraped from Reddit
(4 of 7) and Recraft v3 (4 of 5).

Caveat: the benchmark holdout is a different distribution from our test set (original files, not re-encoded), so the
two accuracies should not be compared as "seen vs unseen" alone.

### 12.5 Robustness to compression and edits (RQ4)

Validation split, n = 468, frozen ensemble. Every image (both classes) was perturbed before scoring.
Source: `evaluation/results/20261009-233447-robustness-ensemble-v3b/robustness.md`.

| Perturbation | Accuracy | FPR | FNR | ROC-AUC |
|---|---|---|---|---|
| original | 0.904 | 0.095 | 0.097 | 0.964 |
| JPEG q90 | 0.895 | 0.091 | 0.120 | 0.958 |
| JPEG q70 | 0.872 | 0.054 | 0.208 | 0.952 |
| JPEG q50 | 0.825 | 0.033 | 0.327 | 0.944 |
| JPEG q30 | 0.776 | 0.017 | 0.447 | 0.936 |
| downscale ×0.5 | 0.904 | 0.095 | 0.097 | 0.963 |
| downscale ×0.25 | 0.889 | 0.091 | 0.133 | 0.956 |
| center crop 60% | 0.844 | 0.107 | 0.208 | 0.930 |
| screenshot (PNG, ×0.5) | 0.904 | 0.095 | 0.097 | 0.963 |

The "original" row is in-sample for the stacking weights, so read the table for *relative* changes only.

### 12.6 Research questions

**RQ1. How accurately can open-source models separate AI images from real photographs?**
Out of the box, most cannot: 7 of 9 public detectors scored ROC-AUC < 0.9 on modern generators. With selection,
transfer learning and an ensemble, we reached ROC-AUC 0.975 and 91.4% accuracy on our test set, and 93.5% on unseen
generators.

**RQ2. Does combining detectors help?**
Yes. On the test set, the best single member (`detector_clip_ft`) reached 89.1% accuracy and FPR 10.8%; the
ensemble reached 91.4% and FPR 7.1%. On the unseen-generator holdout, the best member reached 90.0% and the ensemble
93.5%. Source: `score_*` columns in the two predictions files.

**RQ3. Do detectors generalize to unseen generators?**
Reasonably well with CLIP features. The frozen-CLIP probe was the *strongest* single member on unseen generators
(AUC 0.958), even though it was the weakest in-distribution (0.882 on test). This matches [3]. The fully fine-tuned
model showed the reverse pattern (0.967 on test, 0.931 on unseen).

**RQ4. How do compression and editing affect detection?**
Strong JPEG compression makes AI images look real: at quality 30, FNR rises from 9.7% to 44.7%, while FPR falls.
Downscaling and screenshot-style PNG re-encoding have little effect. Cropping away 40% of the image increases errors
in both classes.

**RQ5. Do uncertainty thresholds reduce false positives?**
Yes. On the test set, FPR fell from 7.1% to 4.2% by abstaining on 11.6% of images. On unseen generators it fell
from 4.1% to 1.7% at 10.5% abstention.

## 13. Implementation and testing

**Stack:** Python 3.13, PyTorch 2.11 (CUDA 12.8), Hugging Face Transformers, timm, FastAPI, SQLAlchemy + SQLite, Vue 3,
Vite, Tailwind CSS, Chart.js. Total software cost: ₹0.

**Pipeline scripts** (`scripts/`): `fetch_training_data`, `fetch_benchmark`, `dataset_tool` (index/split/check),
`download_models`, `evaluate`, `select_detectors`, `train`, `fit_ensemble`, `error_analysis`, `robustness`,
`final_evaluation`. All metrics come from one implementation, `evaluation/metrics.py`.

**Testing:**

`pytest` runs **62 tests**, all passing; they use a fake detector, so no model download is needed.

| Kind | Examples (`backend/tests/`) |
|---|---|
| Unit | decision thresholds and confidence, ensemble combination incl. `logit_stack`, AI-label lookup from `id2label`, SHA-256, safe filenames, colour-mode conversion, transparent PNG flattening, JPEG-quality forensics |
| Validation / edge cases | unsupported and corrupt files, too-large uploads (413), decompression bombs, grayscale and transparent images |
| Integration | `/health`, `/detect` round trip, UNCERTAIN result, cache hit on re-upload, history pagination and filters, statistics, evaluation endpoint |
| Provenance | signed vs tampered C2PA manifests, embedded generation parameters, XMP DigitalSourceType, EXIF generator names, provenance overriding detectors |
| Model | metrics, confusion matrix, ROC curve and CIs on the sealed test and unseen-generator sets (§12) |

The frontend production build (`npm run build`) succeeds.

## 14. Limitations

- **No universal accuracy.** Results hold for OpenFake-style data. New generators may evade the detectors.
- **Compression.** Heavy JPEG compression, common on social media, sharply increases missed AI images (§12.5).
- **Resolution confound.** AI and real images differ in median size in our dataset, so the model may partly rely on
  it.
- **Small, single-source training set.** 3,116 images from one dataset family. The fine-tuned model overfits
  (99.9% train vs 85.9% validation accuracy).
- **Small per-generator samples.** Most generators have fewer than 10 test images.
- **Real-photo false positives** remain at 7% when the system is forced to decide. Accusing a genuine photo is the
  costlier error, so we recommend keeping the UNCERTAIN band.
- **Metadata can be removed.** The provenance check can confirm AI origin but can never prove an image is real.
- **No sealed `test_unseen` split.** The cross-generator result uses the external benchmark holdout instead.
  `ensemble-v1` had already been scored on that holdout once.
- **Forensic features** are displayed but were not evaluated as classifiers.

## 15. Future scope

- More training data from more generators and real-photo sources, with matched resolutions.
- Training with stronger compression augmentation, plus adversarial / social-media laundering.
- Frequency-domain detectors as additional ensemble members.
- Explainability (heatmaps showing which regions drove the score).
- Continual learning as new generators appear.
- A browser extension or mobile app.
- Extension to video and audio deepfakes.

## 16. Conclusion

A free, offline system built from open-source components can detect modern AI-generated images with
ROC-AUC 0.975 on a sealed test set and 93.5% accuracy on unseen generators. On the images where it is confident,
which is about 88% of them, it meets the project's 95% accuracy target and keeps false positives under 5%. The main
practical risk is heavy compression, and the main methodological lesson is that benchmark scores did not transfer
automatically to a differently processed dataset; only error analysis on our own validation data revealed this.

## 17. Definition of Done (plan §52)

- [x] Application runs locally (`run.bat`, port 8765)
- [x] No paid API is required
- [x] Image upload works
- [x] Invalid files are rejected (413/415/400, tested)
- [x] Local AI model performs inference
- [x] AI/REAL prediction works
- [x] Uncertain state works
- [x] Results are stored (SQLite)
- [x] Detection history works (API tested; Vue view builds)
- [x] Dashboard works (statistics API tested; Vue view builds; not re-checked in a browser for this report)
- [x] Dataset is documented (`docs/methodology.md`, `dataset/SOURCES.md`)
- [x] Dataset leakage is checked (`dataset_tool.py check`: no leakage)
- [x] Test set is independent (sealed, run once, `FREEZE.md`)
- [x] Accuracy, precision, recall and F1 are calculated
- [x] Confusion matrix is generated
- [x] Cross-generator evaluation is performed (benchmark holdout; no internal `test_unseen` split)
- [x] False positives are analyzed
- [x] False negatives are analyzed
- [x] Limitations are documented
- [x] Final report is completed
- [x] Source code is version controlled (git)

## References

[1] S.-Y. Wang, O. Wang, R. Zhang, A. Owens, A. A. Efros. "CNN-generated images are surprisingly easy to spot… for
now." *CVPR*, 2020.

[2] R. Corvi, D. Cozzolino, G. Zingarini, G. Poggi, K. Nagano, L. Verdoliva. "On the detection of synthetic images
generated by diffusion models." *ICASSP*, 2023. doi:10.1109/ICASSP49357.2023.10095167. arXiv:2211.00680.

[3] U. Ojha, Y. Li, Y. J. Lee. "Towards Universal Fake Image Detectors that Generalize Across Generative Models."
*CVPR*, 2023.

[4] A. Radford et al. "Learning Transferable Visual Models From Natural Language Supervision." *ICML*, 2021.

[5] A. Dosovitskiy et al. "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale." *ICLR*, 2021.

[6] Z. Liu et al. "Swin Transformer V2: Scaling Up Capacity and Resolution." *CVPR*, 2022.

[7] X. Zhai, B. Mustafa, A. Kolesnikov, L. Beyer. "Sigmoid Loss for Language Image Pre-Training." *ICCV*, 2023.

[8] M. Zhu et al. "GenImage: A Million-Scale Benchmark for Detecting AI-Generated Image." *NeurIPS Datasets and
Benchmarks*, 2023.

[9] V. Livernoche, A. Arodi, A. Musulan, Z. Yang, A. Salvail, G. Marceau Caron, J.-F. Godbout, R. Rabbany. "OpenFake:
An Open Dataset and Platform Toward Real-World Deepfake Detection." arXiv:2509.09495, 2025.
Dataset: https://huggingface.co/datasets/ComplexDataLab/OpenFake

[10] D. H. Wolpert. "Stacked generalization." *Neural Networks* 5(2), 1992.

[11] J. Platt. "Probabilistic outputs for support vector machines and comparisons to regularized likelihood methods."
*Advances in Large Margin Classifiers*, 1999.

[12] Y. Geifman, R. El-Yaniv. "Selective Classification for Deep Neural Networks." *NeurIPS*, 2017.

[13] Coalition for Content Provenance and Authenticity. *C2PA Technical Specification.* https://c2pa.org/specifications/

[14] Model cards: https://huggingface.co/haywoodsloan/ai-image-detector-deploy,
https://huggingface.co/Ateeqq/ai-vs-human-image-detector
