"""
Unit tests for foodlens/scoring.py
Tests:
1. Category-aware score calculation
2. Insufficient data rule (> 2 of 6 components missing -> None / Insufficient data)
3. Reason generation and component points
4. Consistency across versions
"""

from foodlens.nutrition import NutritionProfile, create_nutrient
from foodlens.scoring import calculate_foodlens_score, SCORING_VERSION


def test_insufficient_data_returns_none_score():
    # Only 2 components present (4 missing > 2)
    profile = NutritionProfile(
        basis="per_100g",
        energy_kcal=create_nutrient(400.0, "kcal"),
        protein_g=create_nutrient(5.0, "g"),
    )
    result = calculate_foodlens_score(profile)
    assert result.score is None
    assert result.band == "Insufficient data"
    assert "insufficient" in result.reasons[0].lower() or "missing" in result.reasons[0].lower()


def test_high_sugar_snack_scoring():
    profile = NutritionProfile(
        basis="per_100g",
        energy_kcal=create_nutrient(480.0, "kcal"),
        protein_g=create_nutrient(4.0, "g"),
        carbs_g=create_nutrient(75.0, "g"),
        sugars_g=create_nutrient(35.0, "g"),  # Very high sugar
        fat_g=create_nutrient(20.0, "g"),
        sat_fat_g=create_nutrient(12.0, "g"),  # High sat fat
        sodium_mg=create_nutrient(400.0, "mg"),
        fibre_g=create_nutrient(1.0, "g"),
    )
    result = calculate_foodlens_score(profile, category="biscuits")
    assert result.score is not None
    assert result.score < 50
    assert result.band == "Consume Mindfully"
    assert result.scoring_version == SCORING_VERSION
    assert any("sugar" in r.lower() for r in result.reasons)


def test_nutritious_profile():
    profile = NutritionProfile(
        basis="per_100g",
        energy_kcal=create_nutrient(250.0, "kcal"),
        protein_g=create_nutrient(14.0, "g"),  # High protein
        carbs_g=create_nutrient(35.0, "g"),
        sugars_g=create_nutrient(3.0, "g"),    # Low sugar
        fat_g=create_nutrient(4.0, "g"),
        sat_fat_g=create_nutrient(0.8, "g"),  # Low sat fat
        sodium_mg=create_nutrient(150.0, "mg"), # Low sodium
        fibre_g=create_nutrient(7.5, "g"),    # High fibre
    )
    result = calculate_foodlens_score(profile, category="cereals")
    assert result.score is not None
    assert result.score >= 70
    assert result.band == "Nutritious & Balanced"
