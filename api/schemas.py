"""
Pydantic Schemas for FoodLens REST API
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# --- Scan & Barcode Schemas ---

class BarcodeScanRequest(BaseModel):
    barcode: Optional[str] = Field(None, description="Raw barcode string")


class BarcodeScanResponse(BaseModel):
    found: bool
    source: str
    product: Optional[Dict[str, Any]] = None
    nutrition_profile: Optional[Dict[str, Any]] = None
    validation: Optional[Dict[str, Any]] = None
    score: Optional[Dict[str, Any]] = None
    ingredients: Optional[Dict[str, Any]] = None
    xp_awarded: int = 0
    message: str = ""


class LabelExtractionResponse(BaseModel):
    detected_basis: str
    serving_size_g: Optional[float] = None
    nutrition_profile: Dict[str, Any]
    low_confidence_fields: List[str]
    raw_lines: List[str]
    confidence_scores: Dict[str, float]


class ConfirmScanRequest(BaseModel):
    user_id: int = 1
    barcode: Optional[str] = None
    product_name: str
    brand: str = ""
    category: str = "general"
    net_weight_g: Optional[float] = None
    serving_size_g: Optional[float] = None
    basis: str = "per_100g"
    nutrients: Dict[str, Optional[float]]
    ingredients_text: str = ""
    corrections_made: int = 0


class CalculatePortionRequest(BaseModel):
    product_id: Optional[int] = None
    portion_type: str = "100g"  # 100g, 100ml, serving, packet, custom
    custom_grams: Optional[float] = None
    servings: float = 1.0
    nutrition_data: Optional[Dict[str, Any]] = None


class CompareRequest(BaseModel):
    product_ids: List[int] = Field(..., min_length=2, max_length=4)


class AdviceRequest(BaseModel):
    payload: Dict[str, Any]


class QuestProgressResponse(BaseModel):
    user_id: int
    xp: int
    level: str
    level_icon: str
    next_level_xp: int
    current_streak: int
    longest_streak: int
    streak_freezes: int
    badges: List[Dict[str, Any]]


class QuestAttemptRequest(BaseModel):
    user_id: int = 1
    game_type: str  # guess_sugar, serving_trap
    actual_value: float
    user_guess: float


class QuestAttemptResponse(BaseModel):
    xp_awarded: int
    message: str
    total_xp: int
    level: str


class ErrorResponse(BaseModel):
    error_code: str  # LOW_CONFIDENCE, PRODUCT_NOT_FOUND, VALIDATION_FAILED, INVALID_IMAGE
    message: str
    details: Optional[Dict[str, Any]] = None
