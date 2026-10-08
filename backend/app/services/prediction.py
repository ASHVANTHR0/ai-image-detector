from __future__ import annotations

import time
from dataclasses import dataclass

from PIL import Image

from app.models.ensemble import AI_GENERATED, REAL, Ensemble
from app.services import forensic, provenance
from app.services.preprocessing import to_rgb

PIPELINE_VERSION = "prov1"  # bump when the decision logic changes, so cached results are not reused


@dataclass
class Prediction:
    ai_probability: float
    prediction: str
    confidence: str
    member_scores: dict[str, float]
    forensics: dict | None
    processing_time_ms: int
    model_name: str
    decided_by: str = "detectors"
    model_ai_probability: float | None = None
    provenance: dict | None = None


class PredictionService:
    def __init__(self, ensemble: Ensemble):
        self.ensemble = ensemble

    @property
    def version(self) -> str:
        return f"{self.ensemble.version}+{PIPELINE_VERSION}"

    def run(self, image: Image.Image, data: bytes | None = None, with_forensics: bool = True) -> Prediction:
        start = time.perf_counter()
        rgb = to_rgb(image)
        result = self.ensemble.predict(rgb)
        prov = provenance.check(data, image) if data is not None else {"verdict": None, "signals": []}
        features = forensic.extract(image, rgb) if with_forensics else None

        p, prediction, confidence, decided_by = result.ai_probability, result.prediction, result.confidence, "detectors"
        if prov["verdict"] == AI_GENERATED:
            p, prediction, decided_by = max(p, 0.99), AI_GENERATED, "provenance"
            confidence = "VERIFIED" if prov["strength"] in ("verified", "strong") else "HIGH"
        elif prov["verdict"] == REAL:
            p, prediction, decided_by = min(p, 0.01), REAL, "provenance"
            confidence = "VERIFIED" if prov["strength"] == "verified" else "HIGH"

        elapsed = int(round((time.perf_counter() - start) * 1000))
        return Prediction(p, prediction, confidence, result.member_scores, features, elapsed, self.version,
                          decided_by, result.ai_probability, prov if prov["signals"] else None)
