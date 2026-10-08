"""Individual detectors. Every detector maps a batch of RGB PIL images to ai_probability values in [0, 1]."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

import torch
from PIL import Image

from app.config import PROJECT_DIR

AI_LABEL_KEYWORDS = ("artificial", "ai", "fake", "generated", "ai-generated", "synthetic", "sd", "sdxl")
REAL_LABEL_KEYWORDS = ("human", "hum", "real", "natural", "authentic", "photo")


class Detector(Protocol):
    name: str

    def predict(self, images: list[Image.Image]) -> list[float]: ...


def resolve_device(device: str) -> torch.device:
    if device == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(device)


def find_ai_indices(id2label: dict, override: str | None = None) -> list[int]:
    """Indices of the classes meaning 'not a real photo'. ai_probability is the sum of their probabilities, so
    multi-class detectors (e.g. dalle / sd / real, or AI / Deepfake / Real) work too. Fails loudly instead of guessing."""
    labels = {int(i): str(l).strip().lower() for i, l in id2label.items()}
    if override is not None:
        wanted = {w.strip().lower() for w in override.split(",")}
        matches = [i for i, l in labels.items() if l in wanted]
        if len(matches) != len(wanted):
            raise ValueError(f"ai_label {override!r} not found in {labels}")
        return sorted(matches)
    real = [i for i, l in labels.items() if l in REAL_LABEL_KEYWORDS]
    if len(real) == 1 and len(labels) >= 2:
        return sorted(i for i in labels if i != real[0])
    ai = [i for i, l in labels.items() if l in AI_LABEL_KEYWORDS]
    if len(labels) == 2 and len(ai) == 1:
        return ai
    raise ValueError(f"Cannot tell which labels mean AI in {labels}; set 'ai_label' in the ensemble config")


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_DIR / p


class HFDetector:
    """A Hugging Face image-classification model (pretrained detector, stored locally or as a hub id)."""

    def __init__(self, name: str, path: str, device: torch.device, ai_label: str | None = None):
        from transformers import AutoImageProcessor, AutoModelForImageClassification

        local = _resolve(path)
        source = str(local) if local.exists() else path
        self.name = name
        self.device = device
        self.processor = AutoImageProcessor.from_pretrained(source)
        self.model = AutoModelForImageClassification.from_pretrained(source).to(device).eval()
        self.ai_indices = find_ai_indices(self.model.config.id2label, ai_label)

    @torch.inference_mode()
    def predict(self, images: list[Image.Image]) -> list[float]:
        inputs = self.processor(images=images, return_tensors="pt").to(self.device)
        probs = self.model(**inputs).logits.float().softmax(dim=-1)[:, self.ai_indices].sum(dim=-1)
        return probs.cpu().tolist()


class TimmDetector:
    """A detector fine-tuned by scripts/train.py (timm backbone, single logit = AI)."""

    def __init__(self, name: str, path: str, device: torch.device):
        import timm
        from torchvision import transforms

        folder = _resolve(path)
        info = json.loads((folder / "model_info.json").read_text())
        self.name = name
        self.device = device
        self.model = timm.create_model(info["backbone"], pretrained=False, num_classes=1)
        state = torch.load(folder / info.get("checkpoint", "best.pt"), map_location="cpu", weights_only=True)
        self.model.load_state_dict(state["model"] if "model" in state else state)
        self.model.to(device).eval()
        size = info["input_size"]
        self.transform = transforms.Compose([
            transforms.Resize(int(size * info.get("resize_ratio", 1.14))),
            transforms.CenterCrop(size),
            transforms.ToTensor(),
            transforms.Normalize(info["mean"], info["std"]),
        ])

    @torch.inference_mode()
    def predict(self, images: list[Image.Image]) -> list[float]:
        batch = torch.stack([self.transform(im) for im in images]).to(self.device)
        return torch.sigmoid(self.model(batch).squeeze(1)).float().cpu().tolist()


def build_detector(member: dict, device: torch.device) -> Detector:
    kind = member.get("type", "hf")
    if kind == "hf":
        return HFDetector(member["name"], member["path"], device, member.get("ai_label"))
    if kind == "timm":
        return TimmDetector(member["name"], member["path"], device)
    raise ValueError(f"Unknown detector type {kind!r}")
