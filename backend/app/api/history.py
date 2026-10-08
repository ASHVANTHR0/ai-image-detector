import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.config import get_settings
from app.database.database import Detection, ModelVersion
from app.database.schemas import DetectionOut, DetectionPage, ModelVersionOut, Statistics

router = APIRouter(tags=["history"])
PREDICTIONS = ("AI_GENERATED", "REAL", "UNCERTAIN")


@router.get("/detections", response_model=DetectionPage)
def list_detections(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    prediction: str | None = Query(None, pattern="^(AI_GENERATED|REAL|UNCERTAIN)$"),
    db: Session = Depends(get_db),
) -> DetectionPage:
    query = select(Detection)
    if prediction:
        query = query.where(Detection.prediction == prediction)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(query.order_by(Detection.created_at.desc(), Detection.id.desc()).limit(limit).offset(offset))
    return DetectionPage(total=total, limit=limit, offset=offset, items=[DetectionOut.from_row(r) for r in rows])


@router.get("/detections/{detection_id}", response_model=DetectionOut)
def get_detection(detection_id: int, db: Session = Depends(get_db)) -> DetectionOut:
    row = db.get(Detection, detection_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Detection not found")
    return DetectionOut.from_row(row)


@router.get("/statistics", response_model=Statistics)
def statistics(db: Session = Depends(get_db)) -> Statistics:
    counts = dict(db.execute(select(Detection.prediction, func.count()).group_by(Detection.prediction)).all())
    avg_conf, avg_time = db.execute(select(
        func.avg(func.max(Detection.ai_probability, Detection.real_probability)),
        func.avg(Detection.processing_time_ms),
    )).one()
    histogram = [0] * 10
    for (p,) in db.execute(select(Detection.ai_probability)):
        histogram[min(int(p * 10), 9)] += 1
    times = list(db.scalars(select(Detection.processing_time_ms).order_by(Detection.id.desc()).limit(200)))
    latest = db.scalars(select(ModelVersion).order_by(ModelVersion.id.desc())).first()
    return Statistics(
        total=sum(counts.values()),
        ai_generated=counts.get("AI_GENERATED", 0),
        real=counts.get("REAL", 0),
        uncertain=counts.get("UNCERTAIN", 0),
        average_confidence=avg_conf,
        average_processing_time_ms=avg_time,
        confidence_histogram=histogram,
        processing_times_ms=times[::-1],
        latest_model=ModelVersionOut.model_validate(latest) if latest else None,
    )


@router.get("/evaluation")
def evaluation() -> dict:
    """Offline results on the controlled test sets (written by the final evaluation), not live uploads."""
    path = get_settings().evaluation_summary
    if not path.exists():
        return {"available": False}
    return {"available": True, **json.loads(path.read_text())}
