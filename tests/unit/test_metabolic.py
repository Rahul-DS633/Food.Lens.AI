"""
Unit tests for FoodLens Metabolic Impact Engine (foodlens.metabolic).
Tests deterministic formulas for:
- Protein Density & Protein-to-Energy ratio (PE%).
- Sugar Spike Index (SSI) & Glycemic Buffering.
- Sodium Density & FSSAI HFSS risk.
- Weight Management & Satiety Index (WMI).
"""

import pytest
from foodlens.nutrition import NutritionProfile, Nutrient
from foodlens.metabolic import (
    calculate_protein_density,
    calculate_sugar_spike,
    calculate_sodium_risk,
    calculate_weight_management,
    analyze_metabolic_impact,
)


def _make_nutrient(val, unit="g"):
    return Nutrient(value=val, unit=unit, basis="per_100g", source="api")


@pytest.fixture
def sample_parle_g():
    return NutritionProfile(
        basis="per_100g",
        energy_kcal=_make_nutrient(454.0, "kcal"),
        protein_g=_make_nutrient(6.5, "g"),
        carbs_g=_make_nutrient(78.5, "g"),
        sugars_g=_make_nutrient(26.5, "g"),
        fat_g=_make_nutrient(12.8, "g"),
        sat_fat_g=_make_nutrient(5.8, "g"),
        fibre_g=_make_nutrient(2.1, "g"),
        sodium_mg=_make_nutrient(280.0, "mg"),
        serving_size_g=21.6,
        is_beverage=False
    )


@pytest.fixture
def sample_maggi():
    return NutritionProfile(
        basis="per_100g",
        energy_kcal=_make_nutrient(427.0, "kcal"),
        protein_g=_make_nutrient(8.0, "g"),
        carbs_g=_make_nutrient(63.5, "g"),
        sugars_g=_make_nutrient(2.2, "g"),
        fat_g=_make_nutrient(15.7, "g"),
        sat_fat_g=_make_nutrient(6.8, "g"),
        fibre_g=_make_nutrient(3.6, "g"),
        sodium_mg=_make_nutrient(1020.0, "mg"),
        serving_size_g=70.0,
        is_beverage=False
    )


@pytest.fixture
def sample_frooti():
    return NutritionProfile(
        basis="per_100ml",
        energy_kcal=_make_nutrient(65.0, "kcal"),
        protein_g=_make_nutrient(0.1, "g"),
        carbs_g=_make_nutrient(16.2, "g"),
        sugars_g=_make_nutrient(15.5, "g"),
        fat_g=_make_nutrient(0.0, "g"),
        sat_fat_g=_make_nutrient(0.0, "g"),
        fibre_g=_make_nutrient(0.1, "g"),
        sodium_mg=_make_nutrient(18.0, "mg"),
        serving_size_g=250.0,
        is_beverage=True
    )


@pytest.fixture
def sample_chana():
    # Roasted Bengal Gram (Chana) - High Satiety Benchmark
    return NutritionProfile(
        basis="per_100g",
        energy_kcal=_make_nutrient(380.0, "kcal"),
        protein_g=_make_nutrient(22.0, "g"),
        carbs_g=_make_nutrient(58.0, "g"),
        sugars_g=_make_nutrient(1.2, "g"),
        fat_g=_make_nutrient(6.0, "g"),
        sat_fat_g=_make_nutrient(1.2, "g"),
        fibre_g=_make_nutrient(14.0, "g"),
        sodium_mg=_make_nutrient(45.0, "mg"),
        serving_size_g=50.0,
        is_beverage=False
    )


# ══════════════════════════════════════════════════════════════════════
# 1. Protein Density Tests
# ══════════════════════════════════════════════════════════════════════

def test_protein_density_parle_g(sample_parle_g):
    res = calculate_protein_density(sample_parle_g)
    assert res.protein_energy_pct == 5.7  # (6.5 * 4 / 454) * 100
    assert res.classification == "Critically Diluted"
    assert res.color_hex == "#DC2626"
    assert "Protein Leverage" in res.satiety_impact


def test_protein_density_chana(sample_chana):
    res = calculate_protein_density(sample_chana)
    assert res.protein_energy_pct == 23.2  # (22 * 4 / 380) * 100
    assert res.classification == "High Protein Density"
    assert res.color_hex == "#166534"
    assert res.density_score == 100.0


def test_protein_density_missing_data():
    empty_prof = NutritionProfile(basis="per_100g")
    res = calculate_protein_density(empty_prof)
    assert res.protein_energy_pct is None
    assert res.classification == "Insufficient Data"


# ══════════════════════════════════════════════════════════════════════
# 2. Sugar Spike Index (SSI) Tests
# ══════════════════════════════════════════════════════════════════════

def test_sugar_spike_frooti(sample_frooti):
    res = calculate_sugar_spike(sample_frooti)
    # 250ml portion with 15.5g sugar per 100ml
    assert res.risk_band in ["High", "Severe"]
    assert res.color_hex in ["#EA580C", "#DC2626"]
    assert "spike" in res.explanation.lower()


def test_sugar_spike_buffered_chana(sample_chana):
    res = calculate_sugar_spike(sample_chana)
    assert res.risk_band == "Low"
    assert res.color_hex == "#166534"
    assert res.buffering_factor > 2.0  # High fiber (14g) and protein (22g) buffering


def test_sugar_spike_missing_data():
    empty_prof = NutritionProfile(basis="per_100g")
    res = calculate_sugar_spike(empty_prof)
    assert res.sugar_spike_index is None
    assert res.risk_band == "Insufficient Data"


# ══════════════════════════════════════════════════════════════════════
# 3. Sodium Density & FSSAI HFSS Tests
# ══════════════════════════════════════════════════════════════════════

def test_sodium_risk_maggi(sample_maggi):
    res = calculate_sodium_risk(sample_maggi)
    assert res.is_fssai_hfss_high is True  # 1020 mg > 600 mg
    assert res.color_hex == "#DC2626"
    assert res.daily_limit_pct_per_serving > 30.0  # 70g serving = 714mg (35.7% of 2000mg limit)
    assert "FSSAI HFSS" in res.explanation


def test_sodium_risk_frooti_beverage(sample_frooti):
    # Frooti has 18 mg/100ml (< 50 mg/100ml beverage cutoff)
    res = calculate_sodium_risk(sample_frooti)
    assert res.is_fssai_hfss_high is False
    assert res.color_hex == "#166534"


def test_sodium_risk_missing_data():
    empty_prof = NutritionProfile(basis="per_100g")
    res = calculate_sodium_risk(empty_prof)
    assert res.sodium_mg is None
    assert res.is_fssai_hfss_high is False


# ══════════════════════════════════════════════════════════════════════
# 4. Weight Management & Satiety Index (WMI) Tests
# ══════════════════════════════════════════════════════════════════════

def test_weight_management_parle_g(sample_parle_g):
    res = calculate_weight_management(sample_parle_g)
    assert res.weight_management_index < 40.0
    assert res.verdict == "Low Satiety / Weight Gain Driver"
    assert res.color_hex == "#DC2626"
    assert "Rebound Hunger" in res.hunger_latency


def test_weight_management_chana(sample_chana):
    res = calculate_weight_management(sample_chana)
    assert res.weight_management_index >= 65.0
    assert res.verdict == "Optimal Satiety / Fat Loss Support"
    assert res.color_hex == "#166534"
    assert "Fullness" in res.hunger_latency


# ══════════════════════════════════════════════════════════════════════
# 5. Full Metabolic Impact Orchestrator Tests
# ══════════════════════════════════════════════════════════════════════

def test_full_metabolic_impact_orchestration(sample_parle_g, sample_frooti, sample_chana):
    meta_parle = analyze_metabolic_impact(sample_parle_g)
    assert meta_parle.protein_density.classification == "Critically Diluted"
    assert "diluted protein" in meta_parle.summary_sentence.lower()

    meta_frooti = analyze_metabolic_impact(sample_frooti)
    assert meta_frooti.sugar_spike.risk_band in ["High", "Severe"]

    meta_chana = analyze_metabolic_impact(sample_chana)
    assert meta_chana.weight_management.verdict == "Optimal Satiety / Fat Loss Support"
    assert meta_chana.protein_density.density_score == 100.0
