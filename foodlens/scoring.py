"""
FoodLens Transparent Scoring Engine
Category-aware, versioned, deterministic 6-component scoring algorithm.
Informed by WHO Nutrient Profile and Nutri-Score principles.

Guarantees:
1. Missing data rule: If > 2 of 6 components missing, returns 'Insufficient data'.
2. Never zero-fills missing values.
3. Transparent component point breakdown and human-readable reason list.
4. Disclaimer attached to every score.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
from foodlens.nutrition import NutritionProfile

SCORING_VERSION = "1.0.0"
CONFIG_PATH = Path(__file__).parent / "config" / "category_thresholds.yaml"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)


@dataclass
class ComponentScore:
    name: str
    declared_value: Optional[float]
    unit: str
    points: float  # Negative or positive contribution
    impact: str    # "negative", "positive", "neutral", "missing"
    reason: str


@dataclass
class ScoreResult:
    score: Optional[int]                 # 0-100 or None if insufficient
    band: str                            # e.g. "Nutritious", "Moderate", "Consume Mindfully", "Insufficient data"
    color_hex: str                       # UI color
    scoring_version: str
    components: List[ComponentScore]
    reasons: List[str]
    disclaimer: str = "Educational prototype score based on category nutrient thresholds. Not an official FSSAI or medical diagnostic rating."

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "band": self.band,
            "color_hex": self.color_hex,
            "scoring_version": self.scoring_version,
            "reasons": self.reasons,
            "disclaimer": self.disclaimer,
            "components": [
                {
                    "name": c.name,
                    "declared_value": c.declared_value,
                    "unit": c.unit,
                    "points": c.points,
                    "impact": c.impact,
                    "reason": c.reason,
                }
                for c in self.components
            ],
        }


def normalize_category(category: Optional[str], is_beverage: bool = False) -> str:
    """Resolve product category to known configuration keys."""
    if is_beverage:
        return "beverages"
    if not category:
        return "general"

    cat = category.lower()
    if any(k in cat for k in ("drink", "beverage", "juice", "soda", "water", "tea", "coffee")):
        return "beverages"
    if any(k in cat for k in ("snack", "biscuit", "cookie", "chip", "namkeen", "crisp", "cracker")):
        return "snacks"
    if any(k in cat for k in ("cereal", "muesli", "granola", "oat", "flake", "cornflake")):
        return "cereals"
    return "general"


def calculate_foodlens_score(profile: NutritionProfile, category: Optional[str] = None) -> ScoreResult:
    """
    Computes a transparent 0-100 nutritional quality score.
    Uses 100g/100ml standardized values.
    """
    cat_key = normalize_category(category, is_beverage=profile.is_beverage)
    thresholds = CONFIG.get("categories", {}).get(cat_key, CONFIG["categories"]["general"])

    # 6 Core components
    # Negative: sugars, sat_fat, sodium, energy
    # Positive: protein, fibre
    energy = profile.energy_kcal.value if profile.energy_kcal else None
    sugars = profile.sugars_g.value if profile.sugars_g else None
    sat_fat = profile.sat_fat_g.value if profile.sat_fat_g else None
    sodium = profile.sodium_mg.value if profile.sodium_mg else None
    protein = profile.protein_g.value if profile.protein_g else None
    fibre = profile.fibre_g.value if profile.fibre_g else None

    core_values = [energy, sugars, sat_fat, sodium, protein, fibre]
    missing_count = sum(1 for v in core_values if v is None)

    components: List[ComponentScore] = []
    reasons: List[str] = []

    # Rule: If > 2 of 6 components missing, show "Insufficient data"
    if missing_count > 2:
        return ScoreResult(
            score=None,
            band="Insufficient data",
            color_hex="#9CA3AF",  # slate gray
            scoring_version=SCORING_VERSION,
            components=[],
            reasons=["Insufficient data: label is missing more than 2 core nutritional components (sugar, fat, sodium, protein, or fibre) required for a reliable score."],
        )

    base_points = 70.0  # Starting neutral benchmark

    # 1. Sugars (Negative)
    if sugars is not None:
        th = thresholds["sugars_g"]
        if sugars > th["high"]:
            pts = -25.0
            r = f"High sugar content: {sugars}g / 100g (caution threshold > {th['high']}g)"
            components.append(ComponentScore("Sugar", sugars, "g", pts, "negative", r))
            reasons.append(r)
        elif sugars > th["moderate"]:
            pts = -15.0
            r = f"Moderate sugar: {sugars}g / 100g"
            components.append(ComponentScore("Sugar", sugars, "g", pts, "negative", r))
            reasons.append(r)
        elif sugars <= th["low"]:
            pts = +5.0
            r = f"Low in sugar: {sugars}g / 100g"
            components.append(ComponentScore("Sugar", sugars, "g", pts, "positive", r))
            reasons.append(r)
        else:
            pts = 0.0
            components.append(ComponentScore("Sugar", sugars, "g", pts, "neutral", "Acceptable sugar level"))
        base_points += pts

    # 2. Saturated Fat (Negative)
    if sat_fat is not None:
        th = thresholds["sat_fat_g"]
        if sat_fat > th["high"]:
            pts = -20.0
            r = f"High saturated fat: {sat_fat}g / 100g (caution threshold > {th['high']}g)"
            components.append(ComponentScore("Saturated Fat", sat_fat, "g", pts, "negative", r))
            reasons.append(r)
        elif sat_fat > th["moderate"]:
            pts = -10.0
            r = f"Moderate saturated fat: {sat_fat}g / 100g"
            components.append(ComponentScore("Saturated Fat", sat_fat, "g", pts, "negative", r))
            reasons.append(r)
        else:
            pts = +5.0
            r = f"Low saturated fat: {sat_fat}g / 100g"
            components.append(ComponentScore("Saturated Fat", sat_fat, "g", pts, "positive", r))
            reasons.append(r)
        base_points += pts

    # 3. Sodium (Negative)
    if sodium is not None:
        th = thresholds["sodium_mg"]
        if sodium > th["high"]:
            pts = -20.0
            r = f"High sodium: {sodium}mg / 100g (caution threshold > {th['high']}mg)"
            components.append(ComponentScore("Sodium", sodium, "mg", pts, "negative", r))
            reasons.append(r)
        elif sodium > th["moderate"]:
            pts = -10.0
            r = f"Moderate sodium: {sodium}mg / 100g"
            components.append(ComponentScore("Sodium", sodium, "mg", pts, "negative", r))
            reasons.append(r)
        else:
            pts = +5.0
            r = f"Low sodium: {sodium}mg / 100g"
            components.append(ComponentScore("Sodium", sodium, "mg", pts, "positive", r))
            reasons.append(r)
        base_points += pts

    # 4. Energy Density (Negative if very high)
    if energy is not None:
        th = thresholds["energy_kcal"]
        if energy > th["high"]:
            pts = -10.0
            r = f"High caloric density: {energy} kcal / 100g"
            components.append(ComponentScore("Energy", energy, "kcal", pts, "negative", r))
            reasons.append(r)
        else:
            pts = 0.0
            components.append(ComponentScore("Energy", energy, "kcal", pts, "neutral", "Normal caloric density"))
        base_points += pts

    # 5. Protein (Positive)
    if protein is not None:
        th_p = thresholds["protein_g"]["bonus_threshold"]
        if protein >= th_p:
            pts = +12.0
            r = f"Good source of protein: {protein}g / 100g (≥ {th_p}g)"
            components.append(ComponentScore("Protein", protein, "g", pts, "positive", r))
            reasons.append(r)
        else:
            pts = 0.0
            components.append(ComponentScore("Protein", protein, "g", pts, "neutral", f"Standard protein: {protein}g / 100g"))
        base_points += pts

    # 6. Dietary Fibre (Positive)
    if fibre is not None:
        th_f = thresholds["fibre_g"]["bonus_threshold"]
        if fibre >= th_f:
            pts = +10.0
            r = f"High in dietary fibre: {fibre}g / 100g (≥ {th_f}g)"
            components.append(ComponentScore("Fibre", fibre, "g", pts, "positive", r))
            reasons.append(r)
        else:
            pts = 0.0
            components.append(ComponentScore("Fibre", fibre, "g", pts, "neutral", f"Modest fibre: {fibre}g / 100g"))
        base_points += pts

    # Clamp total score between 5 and 100
    final_score = int(round(max(5.0, min(100.0, base_points))))

    # Determine band and color
    if final_score >= 70:
        band = "Nutritious & Balanced"
        color = "#1B5E3F"  # Deep green
    elif final_score >= 45:
        band = "Moderate / Everyday"
        color = "#F59E0B"  # Amber
    else:
        band = "Consume Mindfully"
        color = "#DC2626"  # Soft red / caution

    return ScoreResult(
        score=final_score,
        band=band,
        color_hex=color,
        scoring_version=SCORING_VERSION,
        components=components,
        reasons=reasons,
    )
