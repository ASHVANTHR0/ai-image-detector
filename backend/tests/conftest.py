import io
import os
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
os.environ["AID_LOAD_MODELS"] = "false"
os.environ["AID_RATE_LIMIT_PER_MINUTE"] = "0"

from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image  # noqa: E402

from app.database.database import make_session_factory  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models.ensemble import Ensemble  # noqa: E402
from app.services.prediction import PredictionService  # noqa: E402


class FakeDetector:
    def __init__(self, name: str, score: float):
        self.name = name
        self.score = score
        self.device = "cpu"

    def predict(self, images):
        return [self.score for _ in images]


def make_ensemble(scores=(0.95, 0.99), t_low=0.1, t_high=0.9) -> Ensemble:
    detectors = [FakeDetector(f"fake_{i}", s) for i, s in enumerate(scores)]
    config = {"version": "test-ensemble", "method": "weighted_average", "t_low": t_low, "t_high": t_high,
              "members": [{"name": d.name, "weight": 1.0} for d in detectors]}
    return Ensemble(config, detectors)


def image_bytes(fmt="PNG", size=(128, 128), mode="RGB", color=(120, 30, 200), **save_kwargs) -> bytes:
    if mode == "RGBA" and len(color) == 3:
        color = (*color, 128)
    elif mode in ("L",):
        color = 100
    elif mode == "CMYK":
        color = (10, 20, 30, 40)
    buf = io.BytesIO()
    Image.new(mode, size, color).save(buf, format=fmt, **save_kwargs)
    return buf.getvalue()


@pytest.fixture
def app(tmp_path):
    application = create_app()
    application.state.session_factory = make_session_factory(f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    application.state.prediction_service = PredictionService(make_ensemble())
    return application


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


def upload(client, data: bytes, filename="photo.png"):
    return client.post("/api/v1/detect", files={"image": (filename, data, "application/octet-stream")})
