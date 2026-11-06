"""
FoodLens Validation Engine
Deterministic validation rules for nutrition facts:
1. Plausible range checks
2. Macro subset relationships (sugars <= carbs, sat_fat <= fat, etc.)
3. Atwater energy balance cross-check (kcal ≈ 4*P + 4*C + 9*F)
4. Unit confusion detection (e.g. g vs mg for sodium)
5. Basis & serving consistency
6. Data quality grading (Grade A: Complete, Grade B: Partial, Grade C: Minimal)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from foodlens.nutrition import NutritionProfile


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class ValidationIssue:
    rule_name: str
    nutrient: str
    message: str
    severity: Severity
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    is_valid: bool
    issues: List[ValidationIssue]
    quality_grade: str  # "A", "B", "C"
    has_errors: bool
    has_warnings: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "quality_grade": self.quality_grade,
            "has_errors": self.has_errors,
            "has_warnings": self.has_warnings,
            "issues": [
                {
                    "rule_name": i.rule_name,
                    "nutrient": i.nutrient,
                    "message": i.message,
                    "severity": i.severity.value,
                    "details": i.details,
                }
                for i in self.issues
            ],
        }


# Standard physiological maximums per 100g (pure lard/oil is 100g fat / ~900 kcal; pure sugar is 100g carbs)
PER_100G_LIMITS = {
    "energy_kcal": (0.0, 950.0),
    "protein_g": (0.0, 100.0),
    "carbs_g": (0.0, 100.0),
    "sugars_g": (0.0, 100.0),
    "added_sugar_g": (0.0, 100.0),
    "fat_g": (0.0, 100.0),
    "sat_fat_g": (0.0, 100.0),
    "trans_fat_g": (0.0, 100.0),
    "fibre_g": (0.0, 100.0),
    "sodium_mg": (0.0, 40000.0),  # Pure salt is 38758 mg Na/100g
}


def validate_nutrition_profile(profile: NutritionProfile) -> ValidationResult:
    """
    Runs all deterministic validation rules against a NutritionProfile.
    Never mutates nutrient values; records provenance and issues cleanly.
    """
    issues: List[ValidationIssue] = []

    # 1. Range Checks
    for field_name, (min_val, max_val) in PER_100G_LIMITS.items():
        nutrient = getattr(profile, field_name, None)
        if nutrient and nutrient.value is not None:
            val = nutrient.value
            if val < min_val:
                issues.append(
                    ValidationIssue(
                        rule_name="Range",
                        nutrient=field_name,
                        message=f"{field_name} value {val} is below minimum allowed {min_val}",
                        severity=Severity.ERROR,
                        details={"value": val, "min": min_val},
                    )
                )
            elif val > max_val:
                issues.append(
                    ValidationIssue(
                        rule_name="Range",
                        nutrient=field_name,
                        message=f"{field_name} value {val} exceeds physiological limit of {max_val} per 100g",
                        severity=Severity.ERROR,
                        details={"value": val, "max": max_val},
                    )
                )

    # 2. Subset Relationships
    # Sugars <= Carbohydrates
    carbs = profile.carbs_g.value if profile.carbs_g else None
    sugars = profile.sugars_g.value if profile.sugars_g else None
    added_sugars = profile.added_sugar_g.value if profile.added_sugar_g else None
    fat = profile.fat_g.value if profile.fat_g else None
    sat_fat = profile.sat_fat_g.value if profile.sat_fat_g else None
    trans_fat = profile.trans_fat_g.value if profile.trans_fat_g else None

    # We allow a small rounding epsilon of 0.5g
    EPS = 0.5

    if sugars is not None and carbs is not None:
        if sugars > (carbs + EPS):
            issues.append(
                ValidationIssue(
                    rule_name="Subset",
                    nutrient="sugars_g",
                    message=f"Total sugars ({sugars}g) cannot exceed total carbohydrates ({carbs}g).",
                    severity=Severity.ERROR,
                    details={"sugars_g": sugars, "carbs_g": carbs},
                )
            )

    if added_sugars is not None and sugars is not None:
        if added_sugars > (sugars + EPS):
            issues.append(
                ValidationIssue(
                    rule_name="Subset",
                    nutrient="added_sugar_g",
                    message=f"Added sugar ({added_sugars}g) cannot exceed total sugar ({sugars}g).",
                    severity=Severity.ERROR,
                    details={"added_sugar_g": added_sugars, "sugars_g": sugars},
                )
            )

    if sat_fat is not None and fat is not None:
        if sat_fat > (fat + EPS):
            issues.append(
                ValidationIssue(
                    rule_name="Subset",
                    nutrient="sat_fat_g",
                    message=f"Saturated fat ({sat_fat}g) cannot exceed total fat ({fat}g).",
                    severity=Severity.ERROR,
                    details={"sat_fat_g": sat_fat, "fat_g": fat},
                )
            )

    if trans_fat is not None and fat is not None:
        if trans_fat > (fat + EPS):
            issues.append(
                ValidationIssue(
                    rule_name="Subset",
                    nutrient="trans_fat_g",
                    message=f"Trans fat ({trans_fat}g) cannot exceed total fat ({fat}g).",
                    severity=Severity.ERROR,
                    details={"trans_fat_g": trans_fat, "fat_g": fat},
                )
            )

    # 3. Sum of Macros per 100g cannot exceed 100g (+ moisture/ash)
    protein = profile.protein_g.value if profile.protein_g else None
    macro_sum = 0.0
    macro_components = 0
    for m in (protein, carbs, fat):
        if m is not None:
            macro_sum += m
            macro_components += 1

    if macro_components == 3 and macro_sum > 105.0:  # allowing 5g lab variance
        issues.append(
            ValidationIssue(
                rule_name="MacroSum",
                nutrient="macros",
                message=f"Sum of protein, carbs, and fat ({macro_sum:.1f}g) exceeds 100g.",
                severity=Severity.WARNING,
                details={"macro_sum": macro_sum},
            )
        )

    # 4. Energy Cross-Check (Atwater general factors)
    # Energy ≈ 4*P + 4*C + 9*F (+ 2*fibre)
    energy = profile.energy_kcal.value if profile.energy_kcal else None
    fibre = profile.fibre_g.value if profile.fibre_g else 0.0

    if energy is not None and protein is not None and carbs is not None and fat is not None:
        calculated_kcal = (4.0 * protein) + (4.0 * carbs) + (9.0 * fat) + (2.0 * (fibre or 0.0))
        discrepancy = abs(energy - calculated_kcal)
        rel_diff = discrepancy / max(energy, 1.0)

        # Tolerance: 20% or 35 kcal (whichever is larger)
        if rel_diff > 0.20 and discrepancy > 35.0:
            issues.append(
                ValidationIssue(
                    rule_name="EnergyCrossCheck",
                    nutrient="energy_kcal",
                    message=(
                        f"Energy discrepancy: declared {energy:.1f} kcal vs "
                        f"calculated {calculated_kcal:.1f} kcal (gap: {discrepancy:.1f} kcal, {rel_diff*100:.1f}%)."
                    ),
                    severity=Severity.WARNING,
                    details={
                        "declared_kcal": energy,
                        "calculated_kcal": round(calculated_kcal, 1),
                        "gap_kcal": round(discrepancy, 1),
                        "relative_gap": round(rel_diff, 3),
                    },
                )
            )

    # 5. Unit Confusion / Extreme Sodium Check
    sodium = profile.sodium_mg.value if profile.sodium_mg else None
    if sodium is not None and sodium > 15000.0:  # > 15g sodium per 100g (only pure salt/baking soda)
        issues.append(
            ValidationIssue(
                rule_name="UnitConfusion",
                nutrient="sodium_mg",
                message=f"Sodium is unusually high ({sodium} mg/100g). Probable mg vs g unit mix-up.",
                severity=Severity.WARNING,
                details={"sodium_mg": sodium},
            )
        )

    # 6. Basis / Serving Check
    if profile.basis == "per_serving":
        if not profile.serving_size_g or profile.serving_size_g <= 0:
            issues.append(
                ValidationIssue(
                    rule_name="Basis",
                    nutrient="serving_size_g",
                    message="Per-serve values must have a valid serving size in grams to scale.",
                    severity=Severity.ERROR,
                    details={"serving_size_g": profile.serving_size_g},
                )
            )

    # 7. Evaluate Data Quality Grade
    # Grade A: Complete (energy, protein, carbs, sugars, fat, and sodium present, no ERROR issues)
    # Grade B: Partial (energy and at least 2 macros present, no fatal ERROR issues)
    # Grade C: Minimal (insufficient macros or fatal ERROR issues)
    has_errors = any(i.severity == Severity.ERROR for i in issues)
    has_warnings = any(i.severity == Severity.WARNING for i in issues)

    core_present = sum(
        1
        for val in (energy, protein, carbs, sugars, fat, sodium)
        if val is not None
    )

    if has_errors:
        grade = "C"
    elif core_present >= 5:
        grade = "A"
    elif core_present >= 3:
        grade = "B"
    else:
        grade = "C"

    is_valid = not has_errors

    return ValidationResult(
        is_valid=is_valid,
        issues=issues,
        quality_grade=grade,
        has_errors=has_errors,
        has_warnings=has_warnings,
    )

