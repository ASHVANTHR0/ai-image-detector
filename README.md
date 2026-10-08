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

| Phase | Status |
|---|---|
| 1 Environment, app skeleton | ✅ done |
| 2 Dataset | ⏳ tooling done (`scripts/dataset_tool.py`); **images still to be collected** |
| 3 Baseline evaluation | ⏳ two pretrained detectors installed; `scripts/evaluate.py` ready; needs the dataset |
| 4 Custom training | ⏳ `scripts/train.py` ready; needs the dataset |
| 5 Ensemble + thresholds | ⏳ `scripts/fit_ensemble.py` ready; **current weights/thresholds are provisional** |
| 6 Error analysis | ⏳ `scripts/error_analysis.py` ready |
| 7 Backend | ✅ done, 43 tests passing |
| 8 Frontend | ✅ done |
| 9 Final evaluation | ⏳ `scripts/final_evaluation.py` ready (run once, at the end) |
| 10 Documentation | ⏳ in progress |

The app works today with two pretrained detectors (`Organika/sdxl-detector`, `umm-maybe/AI-image-detector`) at equal
weights and 10% / 90% thresholds. Those values are **not tuned yet**, so don't quote results from the app until Phases 2–5
are done.

## Setup (Windows)

Requirements: Python 3.11+ (3.13 used), Node.js 20.19+ (22 used), Git. An NVIDIA GPU is optional but recommended.

```powershell
python -m venv venv
venv\Scripts\activate
# PyTorch first: GPU build (CUDA 12.8) or CPU build
pip install torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cu128
#   or: pip install torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cpu
pip install -r backend\requirements.txt
python scripts\download_models.py        # ~700 MB, once; afterwards runs offline
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
scripts/            dataset_tool, download_models, evaluate, train, fit_ensemble, error_analysis, final_evaluation
evaluation/         metrics.py (single metrics implementation) and results/
experiments/        configs/ (training YAML) and one folder per training run
models/             detector_a, detector_b (pretrained), ensemble/ensemble_config.json
dataset/            raw/, manifest.csv (the source of truth for splits)
docs/               architecture.md, methodology.md, experiments.md
```

## Model licenses

`Organika/sdxl-detector` is **CC BY-NC 3.0** (non-commercial use only; fine for academic work).
`umm-maybe/AI-image-detector` is **CC BY 4.0**. Both are recorded in `models/detector_*/source.json` with their exact revisions.
