"""
FoodLens Report Auto-Checks, Consensus & State Machine Engine
Pure Python deterministic logic for analyzing user data correction reports.

Key Principles:
1. Deterministic validation (plausibility, subset rules, unit sanity).
2. Duplicate detection across pending reports.
3. Consensus & OCR priority scoring.
4. Enforces strict state-machine transitions (approved is terminal).
"""

import math
from dataclasses import dataclass
from typing import Any

VALID_STATUS_TRANSITIONS = {
    "pending": {"approved", "rejected", "needs_info", "duplicate"},
    "needs_info": {"approved", "rejected", "duplicate", "pending"},
    "duplicate": set(),    # Terminal state
    "rejected": set(),     # Terminal state
    "approved": set(),     # Terminal state
}

NUTRIENT_FIELDS = {
    "energy_kcal", "protein_g", "carbs_g", "sugars_g", "added_sugar_g",
    "fat_g", "sat_fat_g", "trans_fat_g", "fibre_g", "sodium_mg", "serving_size_g"
}


@dataclass(frozen=True)
class ReportAutoCheckResult:
    is_plausible: bool
    flags: list[str]
    ocr_match_score: float
    duplicate_of_id: int | None = None
    priority_score: float = 1.0


def validate_proposed_field(
    field_name: str,
    proposed_value: str,
    current_nutrients: dict[str, Any] | None = None
) -> ReportAutoCheckResult:
    """
    Checks proposed nutrient or text values for basic plausibility and subset rules.
    """
    flags: list[str] = []
    current_nutrients = current_nutrients or {}

    if field_name in NUTRIENT_FIELDS:
        try:
            val = float(proposed_value)
            if val < 0:
                flags.append("Nutrient value cannot be negative.")
            if field_name != "energy_kcal" and field_name != "sodium_mg" and field_name != "serving_size_g" and val > 100.0:
                flags.append(f"{field_name} exceeds 100g per 100g basis.")

            # Contextual subset validations
            total_sugars = current_nutrients.get("sugars_g")
            carbs = current_nutrients.get("carbs_g")

            if field_name == "added_sugar_g" and total_sugars is not None and val > total_sugars:
                flags.append(f"Proposed added sugar cannot exceed total sugars ({val}g > {total_sugars}g).")

            if field_name == "sugars_g" and carbs is not None and val > carbs:
                flags.append(f"Proposed total sugars cannot exceed total carbohydrates ({val}g > {carbs}g).")

            if field_name == "sat_fat_g" and current_nutrients.get("fat_g") is not None and val > current_nutrients["fat_g"]:
                total_fat = current_nutrients["fat_g"]
                flags.append(f"Proposed saturated fat cannot exceed total fat ({val}g > {total_fat}g).")

        except ValueError:
            flags.append(f"Invalid numeric format for nutrient {field_name}: '{proposed_value}'.")
    else:
        # Non-numeric text fields (e.g. name, brand, barcode)
        if not proposed_value or len(proposed_value.strip()) == 0:
            flags.append("Proposed text value cannot be empty.")
        if len(proposed_value) > 255:
            flags.append("Proposed value exceeds maximum length of 255 characters.")

    is_plausible = len(flags) == 0
    return ReportAutoCheckResult(
        is_plausible=is_plausible,
        flags=flags,
        ocr_match_score=0.0,
        duplicate_of_id=None,
        priority_score=1.0 if is_plausible else 0.5
    )


def detect_duplicate_report(
    field_name: str,
    proposed_value: str,
    existing_reports: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """
    Identifies whether a matching report on the same field exists among pending reports.
    Handles exact string match and float tolerance.
    """
    norm_val = proposed_value.strip().lower()

    for rep in existing_reports:
        if rep.get("status") not in {"pending", "needs_info"}:
            continue
        if rep.get("field") != field_name:
            continue

        existing_val = str(rep.get("proposed_value", "")).strip().lower()
        if existing_val == norm_val:
            return rep

        # Float comparison for nutrients
        try:
            f_prop = float(norm_val)
            f_exist = float(existing_val)
            if math.isclose(f_prop, f_exist, abs_tol=0.01):
                return rep
        except ValueError:
            pass

    return None


def calculate_priority_score(
    consensus_count: int = 1,
    ocr_match_score: float = 0.0,
    has_validation_flags: bool = False
) -> float:
    """
    Computes priority score for admin review queue.
    Higher priority indicates reports supported by OCR and agreed on by multiple users.
    """
    base = 1.0
    consensus_bonus = max(0, consensus_count - 1) * 1.5
    ocr_bonus = ocr_match_score * 2.0
    penalty = 1.0 if has_validation_flags else 0.0

    score = round(base + consensus_bonus + ocr_bonus - penalty, 2)
    return max(0.1, score)


def validate_state_transition(from_state: str, to_state: str) -> bool:
    """
    Validates report status transition according to defined state machine.
    Raises ValueError on illegal transition.
    """
    allowed = VALID_STATUS_TRANSITIONS.get(from_state, set())
    if to_state not in allowed:
        raise ValueError(f"Illegal state transition from '{from_state}' to '{to_state}'. Allowed: {sorted(allowed)}")
    return True
