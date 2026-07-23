"""
Upcycling Recommendation Engine
--------------------------------
Core novelty of ReWear: every donation gets routed toward a meaningful
destination instead of a binary accept/reject.

RecommendationEngine is an abstract interface with one method: recommend().
RuleBasedRecommendationEngine is the concrete implementation used today.
When you later train a learned recommender, implement MLRecommendationEngine
and swap it in get_engine() below — nothing else in the codebase changes.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.schemas.donation import (
    ClothingCategory,
    DefectDetection,
    DefectType,
    QualityDecision,
    UpcyclingSuggestion,
)


@dataclass(frozen=True)
class UpcyclingRule:
    rule_id: str
    category: ClothingCategory
    applicable_defects: frozenset
    max_severity: float
    product_name: str
    description: str
    difficulty: str
    materials: tuple
    priority: int


RULES: list = [
    UpcyclingRule("jeans_tote_bag", ClothingCategory.JEANS, frozenset(), 0.6,
                   "Denim Tote Bag", "Sturdy tote sewn from denim leg panels; ideal for moderate wear.",
                   "medium", ("scissors", "sewing machine", "thread", "fabric glue"), 1),
    UpcyclingRule("jeans_wallet", ClothingCategory.JEANS, frozenset({DefectType.STAIN, DefectType.FADE}), 0.7,
                   "Denim Wallet", "Compact wallet using undamaged pocket sections, hides stains/fade well.",
                   "easy", ("scissors", "needle", "thread", "snap button"), 2),
    UpcyclingRule("jeans_pencil_case", ClothingCategory.JEANS, frozenset({DefectType.TEAR, DefectType.HOLE}), 0.8,
                   "Pencil Case", "Zippered pouch that repurposes small intact denim sections around tears/holes.",
                   "easy", ("scissors", "zipper", "sewing machine"), 3),
    UpcyclingRule("shirt_cushion_cover", ClothingCategory.SHIRT, frozenset(), 0.7,
                   "Cushion Cover", "Buttoned cushion cover using the shirt's front placket as the opening.",
                   "easy", ("scissors", "needle", "thread"), 1),
    UpcyclingRule("shirt_apron", ClothingCategory.SHIRT, frozenset({DefectType.STAIN, DefectType.DIRT}), 0.6,
                   "Kitchen Apron", "Apron pattern that keeps stained areas at the lower back, out of view.",
                   "medium", ("scissors", "sewing machine", "bias tape"), 2),
    UpcyclingRule("tshirt_cleaning_cloth", ClothingCategory.TSHIRT, frozenset(), 1.0,
                   "Reusable Cleaning Cloth", "No-sew cut squares; works even for heavily worn/stained items.",
                   "easy", ("scissors",), 3),
    UpcyclingRule("tshirt_shopping_bag", ClothingCategory.TSHIRT, frozenset({DefectType.NONE, DefectType.FADE}), 0.5,
                   "No-Sew Shopping Bag", "Classic t-shirt-to-tote using cut-and-tie technique, no machine needed.",
                   "easy", ("scissors",), 1),
    UpcyclingRule("saree_shopping_bag", ClothingCategory.SAREE, frozenset(), 0.6,
                   "Saree Shopping Bag", "Foldable shopping bag using the saree's border as decorative trim.",
                   "medium", ("scissors", "sewing machine", "thread"), 1),
    UpcyclingRule("saree_handbag", ClothingCategory.SAREE, frozenset({DefectType.FADE}), 0.5,
                   "Handbag", "Structured handbag with lining; best for lightly faded but structurally sound sarees.",
                   "hard", ("scissors", "sewing machine", "lining fabric", "zipper"), 2),
    UpcyclingRule("blanket_pet_bed", ClothingCategory.BLANKET, frozenset(), 1.0,
                   "Pet Bed", "Folded/quilted pet bed; tolerant of stains, tears, and heavy wear.",
                   "easy", ("scissors", "needle", "thread", "stuffing (optional)"), 1),
    UpcyclingRule("blanket_quilt", ClothingCategory.BLANKET, frozenset({DefectType.FADE}), 0.5,
                   "Patchwork Quilt", "Combine intact blanket sections into a patchwork quilt panel.",
                   "medium", ("scissors", "sewing machine", "thread"), 2),
    UpcyclingRule("curtain_storage_basket", ClothingCategory.CURTAIN, frozenset(), 0.8,
                   "Fabric Storage Basket", "Stiffened fabric basket; hides most surface defects.",
                   "medium", ("scissors", "sewing machine", "interfacing"), 1),
    UpcyclingRule("curtain_organizer", ClothingCategory.CURTAIN, frozenset({DefectType.FADE, DefectType.DIRT}), 0.6,
                   "Hanging Fabric Organizer", "Wall-mounted pocket organizer, ideal for larger curtain panels.",
                   "medium", ("scissors", "sewing machine", "dowel rod"), 2),
]

RECYCLE_FALLBACK = UpcyclingSuggestion(
    product_name="Raw Textile Recycling",
    description=(
        "Item is too damaged for direct upcycling. Route to industrial textile "
        "recycling (fiber reclamation) rather than landfill."
    ),
    difficulty="n/a",
    estimated_materials=[],
    matched_rule_id="fallback_recycle",
)


class RecommendationEngine(ABC):
    @abstractmethod
    def recommend(
        self,
        category: ClothingCategory,
        decision: QualityDecision,
        detections: list,
        max_results: int = 3,
    ) -> list:
        ...


class RuleBasedRecommendationEngine(RecommendationEngine):
    def recommend(
        self,
        category: ClothingCategory,
        decision: QualityDecision,
        detections: list,
        max_results: int = 3,
    ) -> list:
        if decision == QualityDecision.ACCEPT:
            return []

        if decision == QualityDecision.REJECT_RECYCLE:
            return [RECYCLE_FALLBACK]

        detected_types = {d.defect for d in detections if d.defect != DefectType.NONE}
        max_observed_severity = max((d.severity for d in detections), default=0.0)

        candidates = [
            rule for rule in RULES
            if rule.category == category and max_observed_severity <= rule.max_severity
        ]

        def rule_score(rule):
            defect_match = 0 if (rule.applicable_defects & detected_types) or not rule.applicable_defects else 1
            return (defect_match, rule.priority)

        candidates.sort(key=rule_score)

        if not candidates:
            return [RECYCLE_FALLBACK]

        return [
            UpcyclingSuggestion(
                product_name=r.product_name,
                description=r.description,
                difficulty=r.difficulty,
                estimated_materials=list(r.materials),
                matched_rule_id=r.rule_id,
            )
            for r in candidates[:max_results]
        ]


_engine_instance = None


def get_engine() -> RecommendationEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = RuleBasedRecommendationEngine()
    return _engine_instance
