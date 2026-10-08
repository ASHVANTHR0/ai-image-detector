from fastapi import APIRouter, Request

from app.database.schemas import Health

router = APIRouter(tags=["health"])


@router.get("/health", response_model=Health)
def health(request: Request) -> Health:
    service = getattr(request.app.state, "prediction_service", None)
    if service is None:
        return Health(status="degraded", model_loaded=False, model_version=None, device=None, thresholds=None,
                      error=getattr(request.app.state, "model_error", None))
    ensemble = service.ensemble
    device = getattr(ensemble.detectors[0], "device", None) if ensemble.detectors else None
    return Health(status="ok", model_loaded=True, model_version=service.version,
                  device=str(device) if device else None,
                  thresholds={"t_low": ensemble.t_low, "t_high": ensemble.t_high})
