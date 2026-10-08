import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_prediction_service
from app.config import get_settings
from app.database.database import Detection
from app.database.schemas import DetectionOut
from app.services.prediction import PredictionService
from app.utils.hashing import sha256_bytes
from app.utils.validation import read_limited, safe_filename, validate_image_bytes

router = APIRouter(tags=["detection"])
_recent_requests: dict[str, deque] = defaultdict(deque)


def rate_limit(request: Request) -> None:
    limit = get_settings().rate_limit_per_minute
    if limit <= 0:
        return
    now = time.monotonic()
    window = _recent_requests[request.client.host if request.client else "unknown"]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= limit:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many requests, please wait a minute")
    window.append(now)


@router.post("/detect", response_model=DetectionOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(rate_limit)])
async def detect(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    service: PredictionService = Depends(get_prediction_service),
) -> DetectionOut:
    settings = get_settings()
    filename = safe_filename(image.filename)
    data = await read_limited(image, settings.max_upload_bytes)
    file_hash = sha256_bytes(data)

    cached = db.scalars(
        select(Detection)
        .where(Detection.file_hash == file_hash, Detection.model_name == service.version)
        .order_by(Detection.id.desc())
    ).first()
    if cached:
        return DetectionOut.from_row(cached, cached=True)

    decoded = validate_image_bytes(data, filename, settings)
    result = await run_in_threadpool(service.run, decoded, data)

    row = Detection(
        filename=filename,
        file_hash=file_hash,
        prediction=result.prediction,
        ai_probability=round(result.ai_probability, 6),
        real_probability=round(1 - result.ai_probability, 6),
        confidence=result.confidence,
        model_name=result.model_name,
        processing_time_ms=result.processing_time_ms,
        details={"member_scores": result.member_scores, "forensics": result.forensics, "decided_by": result.decided_by,
                 "model_ai_probability": result.model_ai_probability, "provenance": result.provenance},
    )
    db.add(row)
    db.commit()
    return DetectionOut.from_row(row)
