"""
FoodLens Nutrition Engine
Deterministic modeling and portion scaling of nutritional values.

Key Architectural Guarantees:
1. Pure Python, no UI dependencies.
2. Never zero-fill missing values: None remains None.
3. Every nutrient tracks value, unit, basis, source, and confidence.
4. Linear scaling invariant: scale(profile, 100g) == profile (when basis is per_100g).
"""

from dataclasses import dataclass, replace
from typing import Dict, Any, Optional
from foodlens.units import sugar_g_to_teaspoons, sodium_mg_to_salt_g


@dataclass(frozen=True)
class Nutrient:
    """
    Immutable representation of a single nutritional measure.
    """
    value: Optional[float]
    unit: str               # 'g', 'mg', 'kcal', 'kJ'
    basis: str              # 'per_100g', 'per_100ml', 'per_serving', 'custom_portion'
    source: str             # 'api', 'ocr', 'user', 'manual'
    confidence: float = 1.0 # 0.0 to 1.0

    def __post_init__(self):
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")
        if self.value is not None and self.value < 0:
            raise ValueError(f"Nutrient value cannot be negative, got {self.value}")


def scale(n: Optional[Nutrient], grams: float, target_basis: str = "custom") -> Optional[Nutrient]:
    """
    Scale a nutrient linearly from a 100g/100ml basis to `grams`.
    If n is None or n.value is None, returns None. Never zero-fills.
    """
    if n is None:
        return None
    if n.value is None:
        return replace(n, basis=target_basis)
    if grams < 0:
        raise ValueError(f"Grams cannot be negative: {grams}")

    scaled_value = round((n.value * grams) / 100.0, 2)
    return replace(n, value=scaled_value, basis=target_basis)


@dataclass(frozen=True)
class NutritionProfile:
    """
    Complete nutritional profile for a product or portion.
    Standardized per 100g or 100ml as reference basis.
    """
    basis: str  # 'per_100g', 'per_100ml', 'per_serving', 'whole_packet', 'custom'
    energy_kcal: Optional[Nutrient] = None
    protein_g: Optional[Nutrient] = None
    carbs_g: Optional[Nutrient] = None
    sugars_g: Optional[Nutrient] = None
    added_sugar_g: Optional[Nutrient] = None
    fat_g: Optional[Nutrient] = None
    sat_fat_g: Optional[Nutrient] = None
    trans_fat_g: Optional[Nutrient] = None
    fibre_g: Optional[Nutrient] = None
    sodium_mg: Optional[Nutrient] = None
    serving_size_g: Optional[float] = None
    net_weight_g: Optional[float] = None
    is_beverage: bool = False

    @property
    def salt_g(self) -> Optional[float]:
        """Derived salt (g) from sodium (mg)."""
        if self.sodium_mg and self.sodium_mg.value is not None:
            return sodium_mg_to_salt_g(self.sodium_mg.value)
        return None

    @property
    def sugar_teaspoons(self) -> Optional[float]:
        """Equivalent teaspoons of sugar for the current portion."""
        if self.sugars_g and self.sugars_g.value is not None:
            return sugar_g_to_teaspoons(self.sugars_g.value)
        return None

    @property
    def servings_per_pack(self) -> Optional[float]:
        """Number of servings contained in the whole package."""
        if self.net_weight_g and self.serving_size_g and self.serving_size_g > 0:
            return round(self.net_weight_g / self.serving_size_g, 2)
        return None

    def get_nutrient_names(self) -> list[str]:
        return [
            "energy_kcal", "protein_g", "carbs_g", "sugars_g", "added_sugar_g",
            "fat_g", "sat_fat_g", "trans_fat_g", "fibre_g", "sodium_mg"
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to serializable dictionary."""
        data: Dict[str, Any] = {
            "basis": self.basis,
            "serving_size_g": self.serving_size_g,
            "net_weight_g": self.net_weight_g,
            "is_beverage": self.is_beverage,
            "sugar_teaspoons": self.sugar_teaspoons,
            "salt_g": self.salt_g,
            "servings_per_pack": self.servings_per_pack,
            "nutrients": {}
        }
        for field_name in self.get_nutrient_names():
            nutrient: Optional[Nutrient] = getattr(self, field_name)
            if nutrient:
                data["nutrients"][field_name] = {
                    "value": nutrient.value,
                    "unit": nutrient.unit,
                    "basis": nutrient.basis,
                    "source": nutrient.source,
                    "confidence": nutrient.confidence
                }
            else:
                data["nutrients"][field_name] = None
        return data


def create_nutrient(
    value: Optional[float],
    unit: str,
    basis: str = "per_100g",
    source: str = "manual",
    confidence: float = 1.0
) -> Optional[Nutrient]:
    """Helper factory to safely construct a Nutrient or keep None if value is None."""
    if value is None:
        return None
    return Nutrient(value=float(value), unit=unit, basis=basis, source=source, confidence=confidence)


def scale_profile(
    profile: NutritionProfile,
    target_grams: float,
    target_basis_label: str = "custom"
) -> NutritionProfile:
    """
    Scale an entire NutritionProfile from 100g (or 100ml) basis to target_grams.
    If the base profile basis was per_serving, it must be normalized to 100g first.
    None stays None.
    """
    if target_grams < 0:
        raise ValueError(f"Target grams must be non-negative, got {target_grams}")

    scaled_fields: Dict[str, Any] = {
        "basis": target_basis_label,
        "serving_size_g": profile.serving_size_g,
        "net_weight_g": profile.net_weight_g,
        "is_beverage": profile.is_beverage,
    }

    for name in profile.get_nutrient_names():
        nutrient = getattr(profile, name)
        scaled_fields[name] = scale(nutrient, target_grams, target_basis=target_basis_label)

    return NutritionProfile(**scaled_fields)


def calculate_portion(
    profile: NutritionProfile,
    portion_type: str,
    custom_grams: Optional[float] = None,
    servings: float = 1.0
) -> NutritionProfile:
    """
    Calculates nutrition for a designated portion:
    - '100g' / '100ml': standard reference basis
    - 'serving': 1 or N servings (using profile.serving_size_g)
    - 'packet': the entire net weight (profile.net_weight_g)
    - 'custom': user-provided custom_grams
    """
    if portion_type in ("100g", "100ml"):
        return scale_profile(profile, 100.0, target_basis_label=portion_type)

    if portion_type == "serving":
        if not profile.serving_size_g or profile.serving_size_g <= 0:
            raise ValueError("Cannot calculate serving portion: serving_size_g is missing or zero.")
        grams = profile.serving_size_g * servings
        label = f"{servings:g}_serving" if servings != 1.0 else "per_serving"
        return scale_profile(profile, grams, target_basis_label=label)

    if portion_type == "packet":
        if not profile.net_weight_g or profile.net_weight_g <= 0:
            raise ValueError("Cannot calculate whole packet portion: net_weight_g is missing or zero.")
        return scale_profile(profile, profile.net_weight_g, target_basis_label="whole_packet")

    if portion_type == "custom":
        if custom_grams is None or custom_grams <= 0:
            raise ValueError("Custom portion requires positive custom_grams.")
        return scale_profile(profile, custom_grams, target_basis_label=f"{custom_grams}g")

    raise ValueError(f"Unknown portion type: {portion_type}")

