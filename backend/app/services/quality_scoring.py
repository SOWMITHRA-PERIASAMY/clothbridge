"""
Quality Scoring Service — converts defect detections into a 0-100 score
and an accept/repair/reject decision. Kept separate from ML inference so
the scoring policy is independently testable and documentable.
"""
from __future__ import annotations

from app.schemas.donation import DefectDetection, DefectType, QualityDecision

DEFECT_WEIGHTS: dict[DefectType, float] = {
    DefectType.TEAR: 40.0,
    DefectType.HOLE: 35.0,
    DefectType.STAIN: 15.0,
    DefectType.DIRT: 10.0,
    DefectType.FADE: 12.0,
    DefectType.HEAVY_WEAR: 25.0,
    DefectType.NONE: 0.0,
}

ACCEPT_THRESHOLD = 80.0
REPAIR_THRESHOLD = 40.0


def compute_quality_score(detections: list[DefectDetection]) -> float:
    score = 100.0
    for d in detections:
        if d.defect == DefectType.NONE:
            continue
        weight = DEFECT_WEIGHTS.get(d.defect, 20.0)
        penalty = weight * d.severity * d.confidence
        score -= (score * penalty) / 100.0
    return round(max(0.0, min(100.0, score)), 2)


def decide(score: float) -> QualityDecision:
    if score >= ACCEPT_THRESHOLD:
        return QualityDecision.ACCEPT
    if score >= REPAIR_THRESHOLD:
        return QualityDecision.REPAIR_UPCYCLE
    return QualityDecision.REJECT_RECYCLE
