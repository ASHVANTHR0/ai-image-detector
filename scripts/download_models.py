"""Download the pretrained Hugging Face detectors into models/ so the app runs fully offline afterwards.

    python scripts/download_models.py                 # default candidates
    python scripts/download_models.py --only detector_a
"""
import argparse
import json
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES = {
    "detector_a": "Organika/sdxl-detector",
    "detector_b": "umm-maybe/AI-image-detector",
    # Newer candidates (2025-2026), benchmarked by scripts/benchmark_detectors.py
    "ateeqq_siglip": "Ateeqq/ai-vs-human-image-detector",
    "haywoodsloan_swinv2": "haywoodsloan/ai-image-detector-deploy",
    "dima806_vit_real": "dima806/ai_vs_real_image_detection",
    "dima806_vit_human": "dima806/ai_vs_human_generated_image_detection",
    "smogy_swin": "Smogy/SMOGY-Ai-images-detector",
    "nyuad_vit": "NYUAD-ComNets/NYUAD_AI-generated_images_detector",
    "prithiv_siglip2": "prithivMLmods/AI-vs-Deepfake-vs-Real-Siglip2",
}
PATTERNS = ["config.json", "preprocessor_config.json", "model.safetensors", "pytorch_model.bin", "README.md"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", choices=list(CANDIDATES))
    args = ap.parse_args()
    api = HfApi()
    for folder, repo in CANDIDATES.items():
        if args.only and folder not in args.only:
            continue
        target = ROOT / "models" / folder
        info = api.model_info(repo)
        print(f"Downloading {repo}@{info.sha[:10]} -> {target}")
        snapshot_download(repo, revision=info.sha, local_dir=target, allow_patterns=PATTERNS)
        config = json.loads((target / "config.json").read_text())
        (target / "source.json").write_text(json.dumps({
            "repo_id": repo,
            "revision": info.sha,
            "license": (info.card_data or {}).get("license") if info.card_data else None,
            "id2label": config.get("id2label"),
            "architecture": config.get("architectures"),
        }, indent=2))
        prep = target / "preprocessor_config.json"
        if prep.exists() and '"ViTFeatureExtractor"' in prep.read_text():  # class removed in transformers 5
            prep.write_text(prep.read_text().replace('"ViTFeatureExtractor"', '"ViTImageProcessor"'))
        print(f"  id2label = {config.get('id2label')}")


if __name__ == "__main__":
    main()
