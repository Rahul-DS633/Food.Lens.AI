"""
Unit & Property tests for foodlens/nutrition.py and foodlens/units.py
Validates:
1. Linear scaling
2. Scaling by 100g returns original value
3. None stays None (never zero-filled)
4. Whole-packet, serving, and custom gram scaling
5. Unit conversions (kJ<->kcal, mg<->g, salt<->sodium)
"""

import pytest
from hypothesis import given, strategies as st
from foodlens.units import (
    kj_to_kcal, kcal_to_kj, mg_to_g, g_to_mg,
    salt_g_to_sodium_mg, sodium_mg_to_salt_g,
    sugar_g_to_teaspoons
)
from foodlens.nutrition import (
    Nutrient, NutritionProfile, scale, scale_profile, calculate_portion, create_nutrient
)


def test_units_conversion_deterministic():
    # 4.184 kJ = 1 kcal
    assert kj_to_kcal(418.4) == 100.0
    assert kcal_to_kj(100.0) == 418.4
    assert kj_to_kcal(None) is None
    assert kcal_to_kj(None) is None

    # mg <-> g
    assert mg_to_g(500.0) == 0.5
    assert g_to_mg(0.5) == 500.0
    assert mg_to_g(None) is None

    # salt <-> sodium
    # Salt = Sodium * 2.5
    # Sodium = Salt / 2.5 * 1000 mg
    assert salt_g_to_sodium_mg(1.0) == 400.0
    assert sodium_mg_to_salt_g(400.0) == 1.0
    assert salt_g_to_sodium_mg(None) is None

    # Sugar teaspoons: 1 tsp ~ 4g
    assert sugar_g_to_teaspoons(16.0) == 4.0
    assert sugar_g_to_teaspoons(10.0) == 2.5
    assert sugar_g_to_teaspoons(None) is None


def test_nutrient_immutability_and_confidence():
    n = Nutrient(value=10.0, unit="g", basis="per_100g", source="ocr", confidence=0.95)
    with pytest.raises(Exception):
        n.value = 20.0  # dataclass(frozen=True)

    with pytest.raises(ValueError):
        Nutrient(value=10.0, unit="g", basis="per_100g", source="ocr", confidence=1.5)


def test_none_stays_none_invariant():
    """Ensure missing nutrients are never converted to 0.0."""
    n_none = Nutrient(value=None, unit="g", basis="per_100g", source="ocr", confidence=0.8)
    scaled = scale(n_none, 50.0)
    assert scaled.value is None

    profile = NutritionProfile(
        basis="per_100g",
        energy_kcal=create_nutrient(400.0, "kcal"),
        protein_g=None,  # missing
        fibre_g=Nutrient(value=None, unit="g", basis="per_100g", source="api"),
        serving_size_g=30.0,
        net_weight_g=150.0
    )
    scaled_prof = scale_profile(profile, 50.0)
    assert scaled_prof.protein_g is None
    assert scaled_prof.fibre_g.value is None


def test_scale_100g_returns_original():
    """Scaling by 100g must return the exact original value."""
    n = Nutrient(value=24.5, unit="g", basis="per_100g", source="api", confidence=1.0)
    scaled = scale(n, 100.0)
    assert scaled.value == 24.5


def test_portion_calculations():
    profile = NutritionProfile(
        basis="per_100g",
        energy_kcal=create_nutrient(500.0, "kcal"),
        protein_g=create_nutrient(8.0, "g"),
        sugars_g=create_nutrient(20.0, "g"),
        sodium_mg=create_nutrient(400.0, "mg"),
        serving_size_g=25.0,
        net_weight_g=100.0
    )

    # 1 serving (25g)
    serving_portion = calculate_portion(profile, "serving", servings=1.0)
    assert serving_portion.energy_kcal.value == 125.0  # 500 * 25 / 100
    assert serving_portion.protein_g.value == 2.0      # 8 * 25 / 100
    assert serving_portion.sugars_g.value == 5.0       # 20 * 25 / 100
    assert serving_portion.sugar_teaspoons == 1.25 or serving_portion.sugar_teaspoons == 1.2

    # 2 servings (50g)
    double_serving = calculate_portion(profile, "serving", servings=2.0)
    assert double_serving.energy_kcal.value == 250.0

    # Whole packet (100g)
    packet_portion = calculate_portion(profile, "packet")
    assert packet_portion.energy_kcal.value == 500.0
    assert packet_portion.sugars_g.value == 20.0
    assert packet_portion.sugar_teaspoons == 5.0

    # Custom grams (40g)
    custom_portion = calculate_portion(profile, "custom", custom_grams=40.0)
    assert custom_portion.energy_kcal.value == 200.0
    assert custom_portion.sugars_g.value == 8.0


@given(
    val=st.floats(min_value=0.0, max_value=5000.0, allow_nan=False, allow_infinity=False),
    grams=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False)
)
def test_hypothesis_linear_scaling_property(val, grams):
    """Property test: scaling by grams / 100 is linear."""
    n = Nutrient(value=val, unit="g", basis="per_100g", source="manual")
    scaled = scale(n, grams)
    expected = round((val * grams) / 100.0, 2)
    assert scaled.value == expected
