import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import detection, health, history
from app.config import get_settings
from app.database.database import make_session_factory

logger = logging.getLogger("aid")


def load_prediction_service(app: FastAPI) -> None:
    from app.models.ensemble import Ensemble
    from app.services.prediction import PredictionService

    settings = get_settings()
    try:
        ensemble = Ensemble.from_file(settings.ensemble_config, settings.device)
        app.state.prediction_service = PredictionService(ensemble)
        logger.info("Loaded %s with %d detector(s)", ensemble.version, len(ensemble.detectors))
    except Exception as exc:  # keep the API up so /health can report the problem
        logger.exception("Failed to load detection models")
        app.state.model_error = f"{type(exc).__name__}: {exc}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if getattr(app.state, "session_factory", None) is None:
        app.state.session_factory = make_session_factory(settings.database_url)
    if settings.load_models and getattr(app.state, "prediction_service", None) is None:
        load_prediction_service(app)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="AI Image Authenticity Detector", version="1.0.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_methods=["GET", "POST"],
                       allow_headers=["*"])
    for module in (detection, history, health):
        app.include_router(module.router, prefix="/api/v1")
    return app


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
app = create_app()
