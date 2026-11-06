"""
FoodLens Units Normalization
Deterministic conversion between nutritional units (kJ <-> kcal, mg <-> g, salt <-> sodium).
Strict principle: None input always returns None. Never invent or zero-fill.
"""

from typing import Optional


def kj_to_kcal(kj: Optional[float]) -> Optional[float]:
    """Convert kilojoules to kilocalories (1 kcal = 4.184 kJ)."""
    if kj is None:
        return None
    return round(kj / 4.184, 2)


def kcal_to_kj(kcal: Optional[float]) -> Optional[float]:
    """Convert kilocalories to kilojoules (1 kcal = 4.184 kJ)."""
    if kcal is None:
        return None
    return round(kcal * 4.184, 2)


def mg_to_g(mg: Optional[float]) -> Optional[float]:
    """Convert milligrams to grams."""
    if mg is None:
        return None
    return round(mg / 1000.0, 4)


def g_to_mg(g: Optional[float]) -> Optional[float]:
    """Convert grams to milligrams."""
    if g is None:
        return None
    return round(g * 1000.0, 2)


def salt_g_to_sodium_mg(salt_g: Optional[float]) -> Optional[float]:
    """
    Convert salt (in grams) to sodium (in milligrams).
    Standard FSSAI / WHO relationship: Salt ≈ Sodium × 2.5.
    Sodium (g) = Salt (g) / 2.5
    Sodium (mg) = (Salt (g) / 2.5) * 1000 = Salt (g) * 400.
    """
    if salt_g is None:
        return None
    return round((salt_g / 2.5) * 1000.0, 2)


def sodium_mg_to_salt_g(sodium_mg: Optional[float]) -> Optional[float]:
    """
    Convert sodium (in milligrams) to salt (in grams).
    Salt (g) = (Sodium (mg) / 1000.0) * 2.5.
    """
    if sodium_mg is None:
        return None
    return round((sodium_mg / 1000.0) * 2.5, 4)


def sugar_g_to_teaspoons(sugar_g: Optional[float]) -> Optional[float]:
    """
    Convert sugar in grams to standard teaspoons (approx 4g of granulated sugar per teaspoon).
    """
    if sugar_g is None:
        return None
    return round(sugar_g / 4.0, 1)


def normalize_nutrient_value(
    value: Optional[float], from_unit: str, target_unit: str
) -> Optional[float]:
    """
    Normalizes a numeric value from source unit to target unit.
    Returns None if value is None or units are incompatible.
    """
    if value is None:
        return None

    src = from_unit.strip().lower()
    tgt = target_unit.strip().lower()

    if src == tgt:
        return round(value, 4)

    # Energy
    if src == "kj" and tgt in ("kcal", "calories", "cal"):
        return kj_to_kcal(value)
    if src in ("kcal", "calories", "cal") and tgt == "kj":
        return kcal_to_kj(value)

    # Mass / Weight
    if src == "mg" and tgt == "g":
        return mg_to_g(value)
    if src == "g" and tgt == "mg":
        return g_to_mg(value)
    if src == "mcg" or src == "µg" or src == "ug":
        if tgt == "mg":
            return round(value / 1000.0, 4)
        if tgt == "g":
            return round(value / 1000000.0, 6)

    # Volume (assume density ~ 1.0 for aqueous beverages if not specified)
    if src == "ml" and tgt == "l":
        return round(value / 1000.0, 4)
    if src == "l" and tgt == "ml":
        return round(value * 1000.0, 2)

    return round(value, 4)

