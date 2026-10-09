# Architecture

```
Browser (Vue 3 + Tailwind + Chart.js, :5173)
   │  /api/* proxied by Vite
   ▼
FastAPI (:8765)  ── app.main: lifespan loads the ensemble once, creates SQLite tables
   ├─ POST /api/v1/detect          upload → validate → hash → (cache hit?) → preprocess → ensemble → forensics → store
   ├─ GET  /api/v1/detections      paginated history, newest first, ?prediction= filter
   ├─ GET  /api/v1/detections/{id}
   ├─ GET  /api/v1/statistics      counts, averages, histograms, latest model_versions row
   ├─ GET  /api/v1/evaluation      offline final-test results (evaluation/results/final/summary.json)
   └─ GET  /api/v1/health          model loaded? version, device, thresholds
        │
        ├─ utils/validation.py     size limit while streaming (413), extension allow-list + real format sniffing (415),
        │                          pixel limit read from the header before decoding, full decode, min size (400)
        ├─ services/preprocessing  EXIF orientation, alpha flattened on white, 16-bit/CMYK/grayscale → RGB
        ├─ models/detector.py      HFDetector (pretrained HF classifiers), TimmDetector (our fine-tuned models);
        │                          the AI class index comes from id2label, never guessed
        ├─ services/provenance.py  C2PA / IPTC / generation-parameter check; confirmed AI origin overrides detectors
        ├─ models/ensemble.py      weighted average / majority vote / logit_stack, optional Platt calibration, decide()
        ├─ services/forensic.py    EXIF, software tag, generator names in metadata, JPEG quality, noise, FFT ratio
        │                          (shown to the user, never used for the decision)
        └─ database/               SQLAlchemy + SQLite: detections, model_versions
```

## Decision rule

`p = combine(member scores)`. The installed `ensemble-v3b` uses `logit_stack`, a logistic regression over the
members' log-odds: p = σ(b + Σ wᵢ·logit(sᵢ)). Then then `p ≥ t_high → AI_GENERATED`, `p ≤ t_low → REAL`, otherwise `UNCERTAIN`.
Confidence: `HIGH` if decided and `max(p, 1−p) ≥ 0.9`, `MEDIUM` if decided otherwise, `LOW` if uncertain.
Weights, calibration and thresholds live in `models/ensemble/ensemble_config.json` and are fitted on the validation
split by `scripts/fit_ensemble.py`. The scripts import the same `combine`/`decide` code as the API, so offline
results match the app's behaviour.

## Database

`detections(id, filename, file_hash, prediction, ai_probability, real_probability, confidence, model_name,
processing_time_ms, created_at, details JSON)` and `model_versions(id, model_name, version, accuracy, precision,
recall, f1_score, created_at)`. Uploaded images are never written to disk; only the result and the SHA-256 are stored.
A re-upload of the same file with the same model version returns the stored result (`cached: true`).

## Request flow (plan §44)

Upload → validation → preprocessing → provenance → swinv2 → detector_clip → detector_clip_ft → ensemble → confidence → forensics →
SQLite → JSON response → result card in the UI.
