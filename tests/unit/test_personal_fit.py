"""
Unit tests for foodlens/personal_fit.py
Deterministic personal fit calculation, portion scaling relative to ICMR/FSSAI reference intakes,
under-18 safety rules, and allergen alert precedence.
"""

import pytest
from foodlens.nutrition import NutritionProfile, create_nutrient
from foodlens.allergens import AllergenStatus
from foodlens.personal_fit import (
    PersonalFitEngine, UserProfileData, PersonalFitVerdict
)


def _sample_profile(energy=400.0, sugars=15.0, sat_fat=4.0, sodium=400.0, protein=8.0):
    return NutritionProfile(
        basis="per_100g",
        energy_kcal=create_nutrient(energy, "kcal"),
        sugars_g=create_nutrient(sugars, "g"),
        sat_fat_g=create_nutrient(sat_fat, "g"),
        sodium_mg=create_nutrient(sodium, "mg"),
        protein_g=create_nutrient(protein, "g"),
        serving_size_g=25.0,
        net_weight_g=100.0,
    )


def test_linear_scaling_and_reference_percentage():
    engine = PersonalFitEngine()
    profile = _sample_profile(energy=400.0, sugars=20.0, sodium=500.0)
    user = UserProfileData(name="Aarav", age=28, weight_kg=70.0, allergies=[])

    # Test 50g portion
    fit_50g = engine.calculate_fit(
        profile=profile,
        user=user,
        portion_grams=50.0,
        ingredients_text="Wheat Flour, Sugar, Vegetable Oil, Salt"
    )

    # Test 100g portion
    fit_100g = engine.calculate_fit(
        profile=profile,
        user=user,
        portion_grams=100.0,
        ingredients_text="Wheat Flour, Sugar, Vegetable Oil, Salt"
    )

    sugar_flag_50 = next(f for f in fit_50g.nutrient_flags if f.nutrient == "sugars_g")
    sugar_flag_100 = next(f for f in fit_100g.nutrient_flags if f.nutrient == "sugars_g")

    # Linear invariant: 100g has exactly 2x portion value and 2x % of reference compared to 50g
    assert round(sugar_flag_100.portion_value, 2) == round(sugar_flag_50.portion_value * 2, 2)
    assert round(sugar_flag_100.pct_of_reference, 2) == round(sugar_flag_50.pct_of_reference * 2, 2)


def test_missing_nutrient_remains_none_never_zero():
    engine = PersonalFitEngine()
    # Profile with missing sodium and missing added sugar
    profile = NutritionProfile(
        basis="per_100g",
        energy_kcal=create_nutrient(300.0, "kcal"),
        sugars_g=create_nutrient(5.0, "g"),
        sat_fat_g=None,
        sodium_mg=None,
        protein_g=create_nutrient(6.0, "g"),
    )
    user = UserProfileData(name="Neha", age=30, allergies=[])

    fit = engine.calculate_fit(
        profile=profile,
        user=user,
        portion_grams=100.0,
        ingredients_text="Ingredients: Rolled Oats, Dried Fruits."
    )

    # Missing nutrients must be documented in missing_data
    assert "sodium_mg" in fit.missing_data
    assert "sat_fat_g" in fit.missing_data

    # Flags for missing nutrients must NOT exist or must have None
    assert not any(f.nutrient == "sodium_mg" for f in fit.nutrient_flags)
    assert not any(f.nutrient == "sat_fat_g" for f in fit.nutrient_flags)


def test_under_18_disables_calorie_and_weight_guidance():
    engine = PersonalFitEngine()
    profile = _sample_profile(energy=500.0, sugars=35.0, sodium=800.0, protein=10.0)

    # Minor user (age 14) with weight provided
    user_minor = UserProfileData(name="Child User", age=14, weight_kg=48.0, allergies=[])

    fit = engine.calculate_fit(
        profile=profile,
        user=user_minor,
        portion_grams=50.0,
        ingredients_text="Ingredients: Corn Flour, Sugar, Salt."
    )

    # Calorie guidance must be disabled
    assert not any(f.nutrient == "energy_kcal" for f in fit.nutrient_flags)

    # Protein must NOT use weight-based g/kg calculation for minors
    prot_flag = next((f for f in fit.nutrient_flags if f.nutrient == "protein_g"), None)
    if prot_flag:
        assert "per kg" not in prot_flag.reason.lower()

    # Minor protection notice must be present
    assert any("parent" in note.lower() or "under 18" in note.lower() for note in fit.guidance_notes)


def test_adult_weight_based_protein():
    engine = PersonalFitEngine()
    profile = _sample_profile(protein=20.0) # 20g per 100g

    # Adult age 26, 70kg -> Reference protein = 70 * 0.83 = 58.1 g
    user_adult = UserProfileData(name="Adult User", age=26, weight_kg=70.0, allergies=[])

    fit = engine.calculate_fit(
        profile=profile,
        user=user_adult,
        portion_grams=100.0,
        ingredients_text="Ingredients: Soya Chunks, Spices."
    )

    prot_flag = next(f for f in fit.nutrient_flags if f.nutrient == "protein_g")
    assert prot_flag.reference_value == pytest.approx(58.1, 0.1)
    assert prot_flag.pct_of_reference == pytest.approx((20.0 / 58.1) * 100, 0.2)
    assert "70.0 kg" in prot_flag.reason


def test_allergen_alert_overrides_all_other_verdicts():
    engine = PersonalFitEngine()
    # Healthy, low sugar, low sodium profile
    profile = _sample_profile(energy=150.0, sugars=2.0, sat_fat=0.5, sodium=50.0, protein=15.0)

    # User allergic to peanuts
    user_allergic = UserProfileData(name="Allergic Eater", age=22, allergies=["peanut"])

    # Product contains peanut
    fit = engine.calculate_fit(
        profile=profile,
        user=user_allergic,
        portion_grams=50.0,
        ingredients_text="Ingredients: Oats, Peanut Butter, Seeds."
    )

    # Verdict MUST be Allergen alert regardless of good nutrition
    assert fit.verdict == PersonalFitVerdict.ALLERGEN_ALERT
    assert fit.allergen_check.overall_status == AllergenStatus.CONTAINS_YOUR_ALLERGEN


def test_verdict_categories():
    engine = PersonalFitEngine()
    user = UserProfileData(name="Regular Eater", age=25, allergies=[])

    # 1. Moderation item (moderate sugar/sodium)
    prof_mod = _sample_profile(sugars=18.0, sodium=450.0)
    fit_mod = engine.calculate_fit(prof_mod, user, portion_grams=50.0, ingredients_text="Wheat Flour, Sugar")
    assert fit_mod.verdict in (PersonalFitVerdict.FITS_IN_MODERATION, PersonalFitVerdict.FITS_WELL)

    # 2. High sugar & sodium item
    prof_high = _sample_profile(sugars=45.0, sodium=1200.0)
    fit_high = engine.calculate_fit(prof_high, user, portion_grams=100.0, ingredients_text="Sugar, Salt")
    assert fit_high.verdict == PersonalFitVerdict.BETTER_OCCASIONALLY


def test_disclaimer_always_present():
    engine = PersonalFitEngine()
    user = UserProfileData(name="Test", age=30, allergies=[])
    profile = _sample_profile()
    fit = engine.calculate_fit(profile, user, portion_grams=25.0, ingredients_text="Wheat, Water")

    assert "General information, not medical advice" in fit.disclaimer
    assert "Verify on the pack" in fit.disclaimer
