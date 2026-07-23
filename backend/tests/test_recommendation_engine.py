from app.schemas.donation import (
    ClothingCategory,
    DefectDetection,
    DefectType,
    QualityDecision,
)
from app.services.recommendation_engine import RuleBasedRecommendationEngine


def make_engine():
    return RuleBasedRecommendationEngine()


def test_accept_decision_returns_no_suggestions():
    engine = make_engine()
    result = engine.recommend(ClothingCategory.JEANS, QualityDecision.ACCEPT, [])
    assert result == []


def test_reject_decision_returns_recycle_fallback():
    engine = make_engine()
    result = engine.recommend(ClothingCategory.SHIRT, QualityDecision.REJECT_RECYCLE, [])
    assert len(result) == 1
    assert result[0].matched_rule_id == "fallback_recycle"


def test_jeans_with_tear_prefers_defect_aware_rule():
    engine = make_engine()
    detections = [DefectDetection(defect=DefectType.TEAR, confidence=0.9, severity=0.75)]
    result = engine.recommend(ClothingCategory.JEANS, QualityDecision.REPAIR_UPCYCLE, detections)
    assert len(result) > 0
    # pencil_case rule explicitly targets TEAR/HOLE and should rank first
    assert result[0].matched_rule_id == "jeans_pencil_case"


def test_severity_above_all_rule_thresholds_falls_back_to_recycle():
    engine = make_engine()
    detections = [DefectDetection(defect=DefectType.TEAR, confidence=0.95, severity=0.95)]
    result = engine.recommend(ClothingCategory.SAREE, QualityDecision.REPAIR_UPCYCLE, detections)
    assert result[0].matched_rule_id == "fallback_recycle"


def test_unknown_category_still_returns_fallback_not_crash():
    engine = make_engine()
    detections = [DefectDetection(defect=DefectType.STAIN, confidence=0.8, severity=0.3)]
    result = engine.recommend(ClothingCategory.OTHER, QualityDecision.REPAIR_UPCYCLE, detections)
    assert result[0].matched_rule_id == "fallback_recycle"


def test_max_results_is_respected():
    engine = make_engine()
    result = engine.recommend(ClothingCategory.JEANS, QualityDecision.REPAIR_UPCYCLE, [], max_results=1)
    assert len(result) == 1
