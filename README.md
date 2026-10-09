# AI-Generated Image Detection and Authenticity Verification

A completely free, locally deployable system that estimates whether an image is **AI generated**, **real**, or
**uncertain**, using open-source deep-learning detectors combined in an ensemble. No paid API, no cloud: after the
models are downloaded everything runs offline on your computer.

> **Accuracy statement.** No detector is 100% accurate on arbitrary internet images. The project measures accuracy on a
> leakage-free, held-out test set, including generators never seen in training, and reports exactly that. See
> [docs/methodology.md](docs/methodology.md).

Stack: Python · PyTorch · Hugging Face Transformers · timm · FastAPI · SQLite · Vue 3 · Tailwind CSS · Chart.js.
The full plan is in [plan/AI_Image_Detection_Full_Project_Plan.md](plan/AI_Image_Detection_Full_Project_Plan.md).

## Current status

All ten phases are complete. Final report: [docs/final_report.md](docs/final_report.md). Viva notes:
[docs/viva_prep.md](docs/viva_prep.md).

| Phase | Status |
|---|---|
| 1 Environment, app skeleton | ✅ |
| 2 Dataset | ✅ 3,116 OpenFake-train images, group-aware splits, no leakage; plus a 417-image unseen-generator benchmark |
| 3 Baseline evaluation | ✅ 9 pretrained detectors benchmarked |
| 4 Custom training | ✅ CLIP ViT-B/16 linear probe (val AUC 0.853) and full fine-tune (val AUC 0.940) |
| 5 Ensemble + thresholds | ✅ `ensemble-v3b`, logistic stacking fitted on validation |
| 6 Error analysis | ✅ found and reduced real-photo false positives (21.5% → 9.5% on validation) |
| 7 Backend | ✅ 62 tests passing, including the provenance validator |
| 8 Frontend | ✅ |
| 9 Final evaluation | ✅ frozen and run once (`evaluation/results/final/`) |
| 10 Documentation | ✅ report, methodology, architecture, experiments, viva prep |

### How an image is judged

1. **Provenance validator.** Signed C2PA Content Credentials (verified with the official `c2pa` library), IPTC
   DigitalSourceType, or embedded generation parameters (Stable Diffusion, ComfyUI, NovelAI ...). If the file itself
   declares it was AI generated, the answer is *AI generated, verified*. Absence of metadata proves nothing.
2. **Detector ensemble `ensemble-v3b`.** `haywoodsloan/ai-image-detector-deploy` (SwinV2), plus two detectors trained
   here on CLIP ViT-B/16: a frozen-backbone linear probe and a full fine-tune. They are combined by logistic
   stacking over their log-odds. The result is AI if p ≥ 0.74, real if p ≤ 0.23, and uncertain otherwise.

### Measured accuracy

| Test set | n | Accuracy (forced) | 95% CI | FPR | ROC-AUC | Decided images | Accuracy when decided |
|---|---|---|---|---|---|---|---|
| Sealed test (seen generator families) | 466 | **91.4%** | 88.6–94.0% | 7.1% | 0.975 | 88.4% | **95.4%** (FPR 4.2%) |
| Unseen generators (OpenFake benchmark holdout) | 199 | **93.5%** | 90.0–97.0% | 4.1% | 0.971 | 89.5% | **96.6%** (FPR 1.7%) |

Weak spots:
- Heavy JPEG compression: at quality 30, 45% of AI images are missed.
- FLUX.1-dev and FLUX 1.1 Pro.
- Midjourney 7.

No detector is 100% accurate; treat results as strong evidence, not proof. Details and limitations are in
[evaluation/results/final/RESULTS.md](evaluation/results/final/RESULTS.md).

## Setup (Windows)

Requirements: Python 3.11+ (3.13 used), Node.js 20.19+ (22 used), Git. An NVIDIA GPU is optional but recommended.

```powershell
python -m venv venv
venv\Scripts\activate
# PyTorch first: GPU build (CUDA 12.8) or CPU build
pip install torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cu128
#   or: pip install torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cpu
pip install -r backend\requirements.txt
python scripts\download_models.py --only haywoodsloan_swinv2   # pretrained member of the app's ensemble, once
# (no --only = all 10 candidates, ~4 GB, needed only to re-run the benchmark)
# The two CLIP detectors' weights (models/detector_clip*/best.pt) are not in git. Recreate them with
#   python scripts\fetch_training_data.py; python scripts\dataset_tool.py index; python scripts\dataset_tool.py split
#   python scripts\train.py --config experiments\configs\clip_linear.yaml --export models\detector_clip
#   python scripts\train.py --config experiments\configs\clip_vitb16.yaml --export models\detector_clip_ft
cd frontend; npm install; cd ..
```

## Run

Double-click **`run.bat`**. It opens the backend (http://127.0.0.1:8765, API docs at `/docs`) and the frontend
(http://localhost:5173). If the app is already running, it just opens the browser.

To stop it, double-click **`stop.bat`**. It stops both servers and closes their windows. Ctrl + C inside the windows
is unreliable on Windows. Port 8000 isn't used because Splunk occupies it on this machine. To use another backend
port, change it in `run.bat` and set `AID_BACKEND_URL` for the frontend.

Manual start:
```powershell
cd backend;  ..\venv\Scripts\python -m uvicorn app.main:app --port 8765
cd frontend; npm run dev
```

Tests: `cd backend; ..\venv\Scripts\python -m pytest`

## Research workflow

Run all commands from the project root with the venv active. The `test` and `test_unseen` splits are sealed: the
scripts refuse to read them until the final evaluation.

```powershell
# 2. Dataset: put images in dataset/raw/real/<source>/ and dataset/raw/ai/<generator>/, document them in dataset/SOURCES.md
python scripts\dataset_tool.py index
python scripts\dataset_tool.py split --holdout-generators flux     # held-out generators -> test_unseen
python scripts\dataset_tool.py check                               # must report no leakage

# 3. Baseline: score the pretrained detectors on the validation split
python scripts\evaluate.py --run-name baseline

# 4. Train your own detector (transfer learning) and export it for the app
python scripts\train.py --config experiments\configs\convnext_tiny.yaml --export models\detector_c
#    then add {"name": "convnext", "type": "timm", "path": "models/detector_c"} to models/ensemble/ensemble_config.json

# 5. Ensemble weights, calibration, uncertainty thresholds (validation only)
python scripts\evaluate.py --run-name members
python scripts\fit_ensemble.py evaluation\results\<run_id> --version ensemble-v1 --write

# 6. Error analysis -> fix data/augmentation -> retrain -> re-evaluate
python scripts\evaluate.py --run-name check
python scripts\error_analysis.py evaluation\results\<run_id>\predictions.csv

# 9. Once everything is frozen: the one-time final test (seen + unseen generators)
python scripts\final_evaluation.py --confirm
```

Metrics for any predictions file: `python evaluation\metrics.py <predictions.csv> --t-low 0.1 --t-high 0.9 --by generator --plots`

## Project layout

```
backend/app/        FastAPI app: api/ (routes), models/ (detectors, ensemble), services/ (preprocessing,
                    prediction, forensics), database/ (SQLite + schemas), utils/ (validation, hashing)
backend/tests/      pytest suite (fake detector, no model download needed)
frontend/src/       Vue app: views/ (Dashboard, Detect, History, Analytics, About), components/, services/
scripts/            dataset_tool, download_models, evaluate, train, fit_ensemble, error_analysis, robustness, final_evaluation
evaluation/         metrics.py (single metrics implementation) and results/
experiments/        configs/ (training YAML) and one folder per training run
models/             pretrained detectors, detector_clip / detector_clip_ft (trained here), ensemble/ensemble_config.json
dataset/            raw/, manifest.csv (the source of truth for splits)
docs/               final_report.md, viva_prep.md, architecture.md, methodology.md, experiments.md
```

## Data and model licenses

OpenFake (training data and benchmark) is **CC BY-NC 4.0**: non-commercial use only. `haywoodsloan/ai-image-detector-deploy`
is Apache-2.0. Pinned revisions are in `models/*/source.json`.
