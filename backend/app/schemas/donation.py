"""
Pydantic schemas for donation, prediction, and recommendation payloads.
These define the exact contract between Flutter, FastAPI, and Firestore.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ClothingCategory(str, Enum):
    JEANS = "jeans"
    SHIRT = "shirt"
    TSHIRT = "tshirt"
    SAREE = "saree"
    BLANKET = "blanket"
    CURTAIN = "curtain"
    TROUSER = "trouser"
    DRESS = "dress"
    JACKET = "jacket"
    OTHER = "other"


class DefectType(str, Enum):
    TEAR = "tear"
    HOLE = "hole"
    STAIN = "stain"
    DIRT = "dirt"
    FADE = "fade"
    HEAVY_WEAR = "heavy_wear"
    NONE = "none"


class QualityDecision(str, Enum):
    ACCEPT = "accept"
    REPAIR_UPCYCLE = "repair_upcycle"
    REJECT_RECYCLE = "reject_recycle"


class DonationStatus(str, Enum):
    SUBMITTED = "submitted"
    AI_REVIEWED = "ai_reviewed"
    NGO_ACCEPTED = "ngo_accepted"
    NGO_REJECTED = "ngo_rejected"
    PICKED_UP = "picked_up"
    IN_UPCYCLING = "in_upcycling"
    COMPLETED = "completed"
    DISTRIBUTED = "distributed"


class DonationCreate(BaseModel):
    donor_id: str
    category: ClothingCategory
    image_url: str = Field(..., description="Firebase Storage URL of the uploaded image")
    description: Optional[str] = Field(None, max_length=500)

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, v: str) -> str:
        if not v.startswith(("https://", "gs://")):
            raise ValueError("image_url must be a valid Firebase Storage or HTTPS URL")
        return v


class DefectDetection(BaseModel):
    defect: DefectType
    confidence: float = Field(..., ge=0.0, le=1.0)
    severity: float = Field(..., ge=0.0, le=1.0, description="0=negligible, 1=severe")


class QualityReport(BaseModel):
    prediction_id: str
    donation_id: str
    quality_score: float = Field(..., ge=0.0, le=100.0)
    decision: QualityDecision
    detections: list[DefectDetection]
    model_version: str
    inference_confidence: float = Field(..., ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UpcyclingSuggestion(BaseModel):
    product_name: str
    description: str
    difficulty: str
    estimated_materials: list[str]
    matched_rule_id: str


class RecommendationResponse(BaseModel):
    donation_id: str
    category: ClothingCategory
    decision: QualityDecision
    suggestions: list[UpcyclingSuggestion]


class DonationRecord(BaseModel):
    donation_id: str
    donor_id: str
    category: ClothingCategory
    image_url: str
    description: Optional[str] = None
    status: DonationStatus = DonationStatus.SUBMITTED
    quality_report: Optional[QualityReport] = None
    assigned_ngo_id: Optional[str] = None
    assigned_shg_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
