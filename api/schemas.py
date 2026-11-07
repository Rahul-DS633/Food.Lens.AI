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


# --- Personalized Food Fit Schemas ---

class UserProfileCreate(BaseModel):
    user_id: int = 1
    name: str = Field(..., min_length=1, max_length=128, description="Display name, display only")
    age: int = Field(..., ge=1, le=120, description="Age in years (1 to 120)")
    weight_kg: Optional[float] = Field(None, ge=5.0, le=300.0, description="Optional weight in kg")
    allergies: List[str] = Field(default_factory=list, description="List of declared allergen categories")
    custom_allergens: str = Field("", description="Comma-separated custom triggers")
    language: str = Field("en", description="Preferred language ('en' or 'hi')")
    consent_given: bool = Field(False, description="Explicit consent to process dietary preferences")
    parental_consent_given: bool = Field(False, description="Parental / guardian consent (required if age < 18)")


class UserProfileResponse(BaseModel):
    id: int
    user_id: int
    name: str
    age: int
    weight_kg: Optional[float] = None
    allergies: List[str]
    custom_allergens: str
    language: str
    consent_given: bool
    parental_consent_given: bool
    consent_timestamp: Optional[str] = None


class PersonalFitRequest(BaseModel):
    product_id: Optional[int] = None
    portion_type: str = "serving"  # "serving", "100g", "packet", "custom"
    custom_grams: Optional[float] = None
    user_id: Optional[int] = None
    profile_override: Optional[UserProfileCreate] = None
    nutrition_data: Optional[Dict[str, Any]] = None
    ingredients_text: Optional[str] = None


class PersonalFitResponse(BaseModel):
    verdict: str
    portion_grams: float
    confidence: float
    allergen_check: Dict[str, Any]
    nutrient_flags: List[Dict[str, Any]]
    missing_data: List[str]
    guidance_notes: List[str]
    ai_explanation: Optional[Dict[str, Any]] = None
    disclaimer: str


# --- Hidden Sugar Detector Schemas ---

class SugarAnalyzeRequest(BaseModel):
    product_id: Optional[int] = None
    ingredients_text: Optional[str] = None
    portion_g: float = 100.0
    added_sugar_g: Optional[float] = None
    total_sugars_g: Optional[float] = None


class SugarMatchSchema(BaseModel):
    ingredient_text: str
    normalized_alias: str
    sugar_class: str
    position: int
    confidence: float
    match_type: str
    is_added: str
    explanation: str


class SugarReportResponse(BaseModel):
    matches: List[SugarMatchSchema]
    distinct_sugar_names: List[str]
    first_sugar_position: Optional[int] = None
    sugars_in_top3: bool
    sugar_splitting: bool
    non_sugar_sweeteners: List[str]
    carb_fillers: List[str]
    label_conflict: bool
    label_conflict_reason: Optional[str] = None
    portion_teaspoons: Optional[float] = None
    teaspoon_basis: Optional[str] = None
    ai_summary: str
    status: str


# --- Data Reports & Admin Schemas ---

class DataReportSubmitRequest(BaseModel):
    product_id: int
    field: str
    current_value: Optional[str] = None
    proposed_value: str
    comment: Optional[str] = Field(None, max_length=500)
    consent_no_personal_data: bool = True
    reporter_hash: Optional[str] = None


class DataReportResponse(BaseModel):
    id: int
    product_id: int
    field: str
    current_value: Optional[str] = None
    proposed_value: str
    evidence_image_path: Optional[str] = None
    comment: Optional[str] = None
    status: str
    priority_score: float
    auto_checks: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    reviewer_note: Optional[str] = None


class AdminReportReviewRequest(BaseModel):
    reviewer_note: Optional[str] = ""


class AdminMetricsResponse(BaseModel):
    pending_count: int
    approved_count: int
    rejected_count: int
    duplicate_count: int
    needs_info_count: int
    total_reports: int
    approval_rate_percent: float
    most_reported_fields: List[Dict[str, Any]]


# --- Family Profiles & Household Schemas ---

class HouseholdMemberCreate(BaseModel):
    display_name: str
    emoji_avatar: str = "👤"
    age: int = Field(..., ge=1, le=120)
    weight_kg: Optional[float] = Field(None, ge=5.0, le=300.0)
    allergies: List[str] = Field(default_factory=list)
    dietary_prefs: List[str] = Field(default_factory=list)
    consent_by_owner: bool = True


class HouseholdMemberResponse(BaseModel):
    id: int
    household_id: int
    display_name: str
    emoji_avatar: str
    age: int
    weight_kg: Optional[float] = None
    allergies: List[str]
    dietary_prefs: List[str]
    is_minor: bool
    consent_by_owner: bool
    created_at: Optional[str] = None


class HouseholdResponse(BaseModel):
    id: int
    owner_user_id: int
    members: List[HouseholdMemberResponse]
    created_at: Optional[str] = None


class FamilyCheckRequest(BaseModel):
    product_id: int
    member_ids: List[int] = Field(..., min_length=1, max_length=8)
    portions: Dict[int, float] = Field(default_factory=dict)


class FamilyCheckResponse(BaseModel):
    worst_allergen_status: str
    top_alert_banner: str
    summary_sentence: str
    members_evaluated: List[int]
    allergen_matrix: Dict[str, Dict[str, str]]
    disclaimer: str





