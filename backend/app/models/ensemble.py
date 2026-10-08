"""Ensemble decision layer. The decision math lives here only; scripts import it so evaluation matches the API."""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from app.models.detector import Detector, build_detector, resolve_device

AI_GENERATED, REAL, UNCERTAIN = "AI_GENERATED", "REAL", "UNCERTAIN"


def decide(ai_probability: float, t_low: float, t_high: float) -> tuple[str, str]:
    """Return (prediction, confidence) for a calibrated AI probability."""
    if ai_probability >= t_high:
        prediction = AI_GENERATED
    elif ai_probability <= t_low:
        prediction = REAL
    else:
        return UNCERTAIN, "LOW"
    confidence = "HIGH" if max(ai_probability, 1 - ai_probability) >= 0.9 else "MEDIUM"
    return prediction, confidence


def combine(scores: dict[str, float], weights: dict[str, float], method: str = "weighted_average",
            calibration: dict | None = None) -> float:
    if method == "weighted_average":
        total = sum(weights[n] for n in scores)
        p = sum(scores[n] * weights[n] for n in scores) / total
    elif method == "majority_vote":
        votes = [scores[n] >= 0.5 for n in scores]
        p = sum(votes) / len(votes)
    else:
        raise ValueError(f"Unknown ensemble method {method!r}")
    if calibration and calibration.get("type") == "platt":
        logit = math.log(max(p, 1e-6) / max(1 - p, 1e-6))
        p = 1 / (1 + math.exp(-(calibration["a"] * logit + calibration["b"])))
    return p


@dataclass
class EnsembleResult:
    ai_probability: float
    prediction: str
    confidence: str
    member_scores: dict[str, float]


class Ensemble:
    def __init__(self, config: dict, detectors: list[Detector]):
        self.config = config
        self.version: str = config["version"]
        self.method: str = config.get("method", "weighted_average")
        self.t_low: float = config["t_low"]
        self.t_high: float = config["t_high"]
        self.calibration: dict | None = config.get("calibration")
        self.weights = {m["name"]: m.get("weight", 1.0) for m in config["members"]}
        self.detectors = detectors

    @classmethod
    def from_file(cls, path: Path, device: str = "auto") -> "Ensemble":
        config = json.loads(Path(path).read_text())
        dev = resolve_device(device)
        detectors = [build_detector(m, dev) for m in config["members"]]
        return cls(config, detectors)

    def predict(self, image: Image.Image) -> EnsembleResult:
        scores = {d.name: float(d.predict([image])[0]) for d in self.detectors}
        p = combine(scores, self.weights, self.method, self.calibration)
        prediction, confidence = decide(p, self.t_low, self.t_high)
        return EnsembleResult(p, prediction, confidence, scores)
