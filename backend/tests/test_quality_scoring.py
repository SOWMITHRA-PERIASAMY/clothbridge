from app.schemas.donation import DefectDetection, DefectType, QualityDecision
from app.services.quality_scoring import compute_quality_score, decide


def test_no_defects_scores_100_and_accepts():
    score = compute_quality_score([])
    assert score == 100.0
    assert decide(score) == QualityDecision.ACCEPT


def test_severe_tear_pushes_toward_reject():
    detections = [DefectDetection(defect=DefectType.TEAR, confidence=0.95, severity=0.9)]
    score = compute_quality_score(detections)
    assert score < 70
    assert decide(score) in (QualityDecision.REPAIR_UPCYCLE, QualityDecision.REJECT_RECYCLE)


def test_mild_fade_alone_still_accepted_or_repairable():
    detections = [DefectDetection(defect=DefectType.FADE, confidence=0.6, severity=0.2)]
    score = compute_quality_score(detections)
    assert score >= 80
    assert decide(score) == QualityDecision.ACCEPT


def test_score_never_goes_below_zero():
    detections = [
        DefectDetection(defect=DefectType.TEAR, confidence=1.0, severity=1.0),
        DefectDetection(defect=DefectType.HOLE, confidence=1.0, severity=1.0),
        DefectDetection(defect=DefectType.HEAVY_WEAR, confidence=1.0, severity=1.0),
    ]
    score = compute_quality_score(detections)
    assert score >= 0.0


def test_decision_thresholds():
    assert decide(85.0) == QualityDecision.ACCEPT
    assert decide(80.0) == QualityDecision.ACCEPT
    assert decide(79.9) == QualityDecision.REPAIR_UPCYCLE
    assert decide(40.0) == QualityDecision.REPAIR_UPCYCLE
    assert decide(39.9) == QualityDecision.REJECT_RECYCLE
