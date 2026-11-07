"""
Unit tests for foodlens/validation.py
Tests:
1. Plausible range checks
2. Subset errors (sugars > carbs, sat_fat > fat, etc.)
3. Energy cross-check (Atwater factors discrepancy > 20%)
4. Unit confusion (extreme sodium)
5. Missing values remain None, grade assignment (A, B, C)
"""

from foodlens.nutrition import NutritionProfile, create_nutrient
from foodlens.validation import validate_nutrition_profile


def test_valid_profile_grade_a():
    profile = NutritionProfile(
        basis="per_100g",
        energy_kcal=create_nutrient(450.0, "kcal"),
        protein_g=create_nutrient(7.5, "g"),
        carbs_g=create_nutrient(65.0, "g"),
        sugars_g=create_nutrient(22.0, "g"),
        fat_g=create_nutrient(18.0, "g"),
        sat_fat_g=create_nutrient(8.0, "g"),
        sodium_mg=create_nutrient(350.0, "mg"),
    )
    res = validate_nutrition_profile(profile)
    assert res.is_valid is True
    assert res.quality_grade == "A"
    assert not res.has_errors


def test_subset_violation_sugars_exceed_carbs():
    profile = NutritionProfile(
        basis="per_100g",
        energy_kcal=create_nutrient(400.0, "kcal"),
        protein_g=create_nutrient(5.0, "g"),
        carbs_g=create_nutrient(30.0, "g"),
        sugars_g=create_nutrient(50.0, "g"),  # 50g sugars > 30g carbs!
        fat_g=create_nutrient(10.0, "g"),
    )
    res = validate_nutrition_profile(profile)
    assert res.is_valid is False
    assert res.has_errors is True
    assert res.quality_grade == "C"
    assert any(i.rule_name == "Subset" and i.nutrient == "sugars_g" for i in res.issues)


def test_subset_violation_sat_fat_exceeds_fat():
    profile = NutritionProfile(
        basis="per_100g",
        energy_kcal=create_nutrient(400.0, "kcal"),
        fat_g=create_nutrient(10.0, "g"),
        sat_fat_g=create_nutrient(15.0, "g"),  # 15g sat fat > 10g total fat!
    )
    res = validate_nutrition_profile(profile)
    assert res.is_valid is False
    assert any(i.rule_name == "Subset" and i.nutrient == "sat_fat_g" for i in res.issues)


def test_range_check_exceeding_100g():
    profile = NutritionProfile(
        basis="per_100g",
        carbs_g=create_nutrient(120.0, "g"),  # > 100g per 100g!
    )
    res = validate_nutrition_profile(profile)
    assert res.is_valid is False
    assert any(i.rule_name == "Range" and i.nutrient == "carbs_g" for i in res.issues)


def test_energy_cross_check_warning():
    # Declared 800 kcal, but macros 5g protein, 10g carbs, 5g fat = 4*5 + 4*10 + 9*5 = 105 kcal
    profile = NutritionProfile(
        basis="per_100g",
        energy_kcal=create_nutrient(800.0, "kcal"),
        protein_g=create_nutrient(5.0, "g"),
        carbs_g=create_nutrient(10.0, "g"),
        fat_g=create_nutrient(5.0, "g"),
        sodium_mg=create_nutrient(100.0, "mg"),
    )
    res = validate_nutrition_profile(profile)
    assert res.has_warnings is True
    assert any(i.rule_name == "EnergyCrossCheck" for i in res.issues)


def test_unit_confusion_extreme_sodium():
    profile = NutritionProfile(
        basis="per_100g",
        energy_kcal=create_nutrient(300.0, "kcal"),
        protein_g=create_nutrient(5.0, "g"),
        carbs_g=create_nutrient(50.0, "g"),
        fat_g=create_nutrient(10.0, "g"),
        sodium_mg=create_nutrient(25000.0, "mg"),  # 25g sodium in 100g!
    )
    res = validate_nutrition_profile(profile)
    assert any(i.rule_name == "UnitConfusion" for i in res.issues)

