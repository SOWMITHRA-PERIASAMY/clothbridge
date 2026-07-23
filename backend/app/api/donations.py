"""
Donation + Prediction + Recommendation endpoints.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.ml.inference import ClothingQualityModel, ModelNotTrainedError
from app.schemas.donation import (
    DonationCreate,
    DonationRecord,
    DonationStatus,
    QualityReport,
    RecommendationResponse,
)
from app.services.quality_scoring import compute_quality_score, decide
from app.services.recommendation_engine import get_engine
from app.services.repository import DonationRepository, get_repository

router = APIRouter(prefix="/donations", tags=["donations"])


@router.post("", response_model=DonationRecord, status_code=status.HTTP_201_CREATED)
def create_donation(
    payload: DonationCreate,
    repo: DonationRepository = Depends(get_repository),
) -> DonationRecord:
    record = DonationRecord(
        donation_id=str(uuid.uuid4()),
        donor_id=payload.donor_id,
        category=payload.category,
        image_url=payload.image_url,
        description=payload.description,
        status=DonationStatus.SUBMITTED,
    )
    repo.save(record)
    return record


@router.get("/{donation_id}", response_model=DonationRecord)
def get_donation(
    donation_id: str,
    repo: DonationRepository = Depends(get_repository),
) -> DonationRecord:
    record = repo.get(donation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Donation not found")
    return record


@router.get("/donor/{donor_id}/history", response_model=list[DonationRecord])
def donation_history(
    donor_id: str,
    repo: DonationRepository = Depends(get_repository),
) -> list[DonationRecord]:
    return repo.list_by_donor(donor_id)


@router.post("/{donation_id}/predict", response_model=QualityReport)
def run_prediction(
    donation_id: str,
    repo: DonationRepository = Depends(get_repository),
) -> QualityReport:
    record = repo.get(donation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Donation not found")

    model = ClothingQualityModel()
    if not model.is_trained:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "No trained model available yet. Run ml_pipeline/train.py "
                "(locally or on Colab) and place model.tflite + labels.txt "
                "in backend/app/ml/artifacts/."
            ),
        )

    from app.ml.preprocessing import load_and_preprocess_image
    try:
        image_array = load_and_preprocess_image(record.image_url)
        detections = model.predict(image_array)
    except ModelNotTrainedError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not process image: {e}",
        )

    score = compute_quality_score(detections)
    decision = decide(score)

    report = QualityReport(
        prediction_id=str(uuid.uuid4()),
        donation_id=donation_id,
        quality_score=score,
        decision=decision,
        detections=detections,
        model_version=model.model_version(),
        inference_confidence=max((d.confidence for d in detections), default=0.0),
    )

    record.quality_report = report
    record.status = DonationStatus.AI_REVIEWED
    repo.save(record)
    return report


@router.get("/{donation_id}/recommendations", response_model=RecommendationResponse)
def get_recommendations(
    donation_id: str,
    repo: DonationRepository = Depends(get_repository),
) -> RecommendationResponse:
    record = repo.get(donation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Donation not found")
    if record.quality_report is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Run /predict for this donation before requesting recommendations",
        )

    engine = get_engine()
    suggestions = engine.recommend(
        category=record.category,
        decision=record.quality_report.decision,
        detections=record.quality_report.detections,
    )
    return RecommendationResponse(
        donation_id=donation_id,
        category=record.category,
        decision=record.quality_report.decision,
        suggestions=suggestions,
    )
