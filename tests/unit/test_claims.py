"""
Unit Tests for Claim Checker Engine
Validates marketing claim detection against verified nutrition and ingredient data.

Rules Tested:
- Sugar claims (sugar_free, low_sugar, no_added_sugar)
- Protein claims (source_of_protein, high_protein)
- Fibre claims (source_of_fibre, high_fibre)
- Fat claims (fat_free, low_fat, low_saturated_fat, no_trans_fat)
- Sodium claims (low_sodium)
- Ingredient claims (whole_grain, multigrain, no_maida, no_preservatives, no_artificial_colours, contains_real_fruit)
- Vague buzzwords (natural, healthy, wholesome -> NOT_CHECKABLE)
- Missing data invariant (CANNOT_VERIFY when nutrient is missing)
- Hindi alias matching
- Linear scaling for per-serving inputs
"""

import pytest
from foodlens.claims import (
    ClaimChecker,
    ClaimStatus,
    ClaimResult,
    ClaimCheckSummary,
)
from foodlens.nutrition import NutritionProfile, create_nutrient


def create_test_profile(
    energy=100.0,
    protein=None,
    carbs=None,
    sugars=None,
    added_sugar=None,
    fat=None,
    sat_fat=None,
    trans_fat=None,
    fibre=None,
    sodium=None,
    basis="per_100g",
    serving_size_g=None,
    category="general",
) -> NutritionProfile:
    return NutritionProfile(
        basis=basis,
        energy_kcal=create_nutrient(energy, "kcal", basis) if energy is not None else None,
        protein_g=create_nutrient(protein, "g", basis) if protein is not None else None,
        carbs_g=create_nutrient(carbs, "g", basis) if carbs is not None else None,
        sugars_g=create_nutrient(sugars, "g", basis) if sugars is not None else None,
        added_sugar_g=create_nutrient(added_sugar, "g", basis) if added_sugar is not None else None,
        fat_g=create_nutrient(fat, "g", basis) if fat is not None else None,
        sat_fat_g=create_nutrient(sat_fat, "g", basis) if sat_fat is not None else None,
        trans_fat_g=create_nutrient(trans_fat, "g", basis) if trans_fat is not None else None,
        fibre_g=create_nutrient(fibre, "g", basis) if fibre is not None else None,
        sodium_mg=create_nutrient(sodium, "mg", basis) if sodium is not None else None,
        serving_size_g=serving_size_g,
        is_beverage=(category == "beverage"),
    )


class TestClaimChecker:
    @pytest.fixture(autouse=True)
    def setup_checker(self):
        self.checker = ClaimChecker()

    # --- SUGAR CLAIMS ---

    def test_sugar_free_supported_at_or_below_0_5g(self):
        profile = create_test_profile(sugars=0.4)
        summary = self.checker.check_claims(["Sugar Free"], profile)
        assert len(summary.results) == 1
        res = summary.results[0]
        assert res.rule_id == "sugar_free"
        assert res.status == ClaimStatus.SUPPORTED
        assert res.threshold_value == 0.5
        assert "FSSAI" in res.threshold_source

    def test_sugar_free_not_supported_above_0_5g(self):
        profile = create_test_profile(sugars=1.2)
        summary = self.checker.check_claims(["Zero Sugar"], profile)
        res = summary.results[0]
        assert res.status == ClaimStatus.NOT_SUPPORTED
        assert "do not appear to support" in res.neutral_explanation

    def test_sugar_free_cannot_verify_when_missing(self):
        profile = create_test_profile(sugars=None)
        summary = self.checker.check_claims(["0% Sugar"], profile)
        res = summary.results[0]
        assert res.status == ClaimStatus.CANNOT_VERIFY
        assert "sugars_g" in res.missing_fields

    def test_no_added_sugar_supported_when_zero_added_and_no_syrups(self):
        profile = create_test_profile(
            added_sugar=0.0,
            sugars=2.0,  # naturally occurring
        )
        summary = self.checker.check_claims(
            ["No Added Sugar"],
            profile,
            ingredients_text="whole oats, freeze dried strawberries, chia seeds"
        )
        res = summary.results[0]
        assert res.rule_id == "no_added_sugar"
        assert res.status == ClaimStatus.SUPPORTED

    def test_no_added_sugar_not_supported_when_syrup_present(self):
        profile = create_test_profile(
            added_sugar=0.0,  # label unstated or misleadingly listed 0
            sugars=15.0,
        )
        summary = self.checker.check_claims(
            ["Without Added Sugar"],
            profile,
            ingredients_text="rolled oats, high fructose corn syrup, almond slivers"
        )
        res = summary.results[0]
        assert res.status == ClaimStatus.NOT_SUPPORTED
        assert "do not appear to support" in res.neutral_explanation

    # --- PROTEIN CLAIMS ---

    def test_high_protein_supported(self):
        profile = create_test_profile(protein=14.0)
        summary = self.checker.check_claims(["High Protein"], profile)
        res = summary.results[0]
        assert res.rule_id == "high_protein"
        assert res.status == ClaimStatus.SUPPORTED
        assert res.threshold_value == 12.0

    def test_high_protein_not_supported_below_12g(self):
        profile = create_test_profile(protein=8.0)
        summary = self.checker.check_claims(["Rich in Protein"], profile)
        res = summary.results[0]
        assert res.status == ClaimStatus.NOT_SUPPORTED

    def test_source_of_protein_supported(self):
        profile = create_test_profile(protein=7.5)
        summary = self.checker.check_claims(["Source of Protein"], profile)
        res = summary.results[0]
        assert res.rule_id == "source_of_protein"
        assert res.status == ClaimStatus.SUPPORTED
        assert res.threshold_value == 6.0

    # --- FIBRE CLAIMS ---

    def test_high_fibre_supported_and_not_supported(self):
        p_high = create_test_profile(fibre=7.2)
        res_high = self.checker.check_claims(["High Fibre"], p_high).results[0]
        assert res_high.status == ClaimStatus.SUPPORTED

        p_low = create_test_profile(fibre=4.0)
        res_low = self.checker.check_claims(["High Fiber"], p_low).results[0]
        assert res_low.status == ClaimStatus.NOT_SUPPORTED

    def test_source_of_fibre_supported(self):
        p = create_test_profile(fibre=3.5)
        res = self.checker.check_claims(["Source of dietary fiber"], p).results[0]
        assert res.status == ClaimStatus.SUPPORTED

    # --- FAT CLAIMS ---

    def test_fat_free_and_low_fat(self):
        p_free = create_test_profile(fat=0.3)
        res_free = self.checker.check_claims(["Fat Free"], p_free).results[0]
        assert res_free.status == ClaimStatus.SUPPORTED

        p_low = create_test_profile(fat=2.5)
        res_low = self.checker.check_claims(["Low Fat"], p_low).results[0]
        assert res_low.status == ClaimStatus.SUPPORTED

        p_high = create_test_profile(fat=8.0)
        res_high = self.checker.check_claims(["Low in Fat"], p_high).results[0]
        assert res_high.status == ClaimStatus.NOT_SUPPORTED

    def test_trans_fat_free(self):
        p_zero = create_test_profile(trans_fat=0.1)
        res_zero = self.checker.check_claims(["Zero Trans Fat"], p_zero).results[0]
        assert res_zero.status == ClaimStatus.SUPPORTED

        p_fail = create_test_profile(trans_fat=0.5)
        res_fail = self.checker.check_claims(["0g Trans Fat"], p_fail).results[0]
        assert res_fail.status == ClaimStatus.NOT_SUPPORTED

    # --- SODIUM CLAIMS ---

    def test_low_sodium(self):
        p_ok = create_test_profile(sodium=110.0)
        res_ok = self.checker.check_claims(["Low Sodium"], p_ok).results[0]
        assert res_ok.status == ClaimStatus.SUPPORTED

        p_high = create_test_profile(sodium=350.0)
        res_high = self.checker.check_claims(["Low Salt"], p_high).results[0]
        assert res_high.status == ClaimStatus.NOT_SUPPORTED

    # --- INGREDIENT & WHOLE GRAIN CLAIMS ---

    def test_whole_grain_primary_supported(self):
        profile = create_test_profile()
        res = self.checker.check_claims(
            ["100% Whole Wheat"],
            profile,
            ingredients_text="Whole wheat flour (atta 90%), water, yeast, salt"
        ).results[0]
        assert res.rule_id == "whole_grain"
        assert res.status == ClaimStatus.SUPPORTED

    def test_whole_grain_secondary_partly_supported(self):
        profile = create_test_profile()
        res = self.checker.check_claims(
            ["Whole Wheat"],
            profile,
            ingredients_text="Refined wheat flour (maida 60%), whole wheat flour (atta 20%), sugar, palm oil"
        ).results[0]
        assert res.status == ClaimStatus.PARTLY_SUPPORTED
        assert "position" in res.neutral_explanation.lower()

    def test_multigrain_evaluation(self):
        p_multi = create_test_profile()
        res_multi = self.checker.check_claims(
            ["Multigrain"],
            p_multi,
            ingredients_text="Wheat, oats, ragi, barley, salt"
        ).results[0]
        assert res_multi.status == ClaimStatus.SUPPORTED

        p_single = create_test_profile()
        res_single = self.checker.check_claims(
            ["Multigrain"],
            p_single,
            ingredients_text="Refined wheat flour, sugar, palm oil"
        ).results[0]
        assert res_single.status == ClaimStatus.NOT_SUPPORTED

    def test_no_maida_exclusion(self):
        p_no_maida = create_test_profile()
        res_ok = self.checker.check_claims(
            ["No Maida"],
            p_no_maida,
            ingredients_text="Whole wheat flour, water, yeast"
        ).results[0]
        assert res_ok.status == ClaimStatus.SUPPORTED

        p_has_maida = create_test_profile()
        res_bad = self.checker.check_claims(
            ["0% Maida"],
            p_has_maida,
            ingredients_text="Maida, sugar, butter"
        ).results[0]
        assert res_bad.status == ClaimStatus.NOT_SUPPORTED

    # --- VAGUE / NON-CHECKABLE BUZZWORDS ---

    def test_vague_marketing_terms_not_checkable(self):
        profile = create_test_profile()
        summary = self.checker.check_claims(
            ["100% Natural", "Healthy", "Wholesome"],
            profile,
            ingredients_text="Apples, water"
        )
        assert len(summary.results) == 3
        for res in summary.results:
            assert res.status == ClaimStatus.NOT_CHECKABLE
            assert "statutory nutrition thresholds" in res.neutral_explanation

    # --- HINDI ALIAS MATCHING ---

    def test_hindi_claim_aliases(self):
        profile = create_test_profile(
            sugars=0.2,
            protein=15.0,
            sodium=80.0,
        )
        summary = self.checker.check_claims(
            ["बिना चीनी", "उच्च प्रोटीन", "कम नमक"],
            profile,
            ingredients_text="साबुत गेहूं का आटा, पानी, नमक"
        )
        assert len(summary.results) == 3
        statuses = [r.status for r in summary.results]
        assert statuses == [ClaimStatus.SUPPORTED, ClaimStatus.SUPPORTED, ClaimStatus.SUPPORTED]

    # --- PER-SERVING LINEAR CONVERSION ---

    def test_per_serving_conversion_when_serving_size_known(self):
        # 3.0g protein in 25g serving -> 12.0g per 100g -> meets high_protein (>= 12.0g)
        profile = create_test_profile(
            protein=3.0,
            basis="per_serving",
            serving_size_g=25.0
        )
        res = self.checker.check_claims(["High Protein"], profile).results[0]
        assert res.status == ClaimStatus.SUPPORTED
        assert res.evidence[0].basis == "scaled_to_100g_from_serving"
        assert res.evidence[0].value == 12.0

    def test_per_serving_cannot_verify_when_serving_size_missing(self):
        profile = create_test_profile(
            protein=3.0,
            basis="per_serving",
            serving_size_g=None
        )
        res = self.checker.check_claims(["High Protein"], profile).results[0]
        assert res.status == ClaimStatus.CANNOT_VERIFY
        assert "serving_size_g" in res.missing_fields

    # --- SUMMARY STATS & DISCLAIMER ---

    def test_check_summary_aggregates(self):
        profile = create_test_profile(
            sugars=0.1,  # supported
            protein=4.0, # not supported (high protein needs 12g)
            fibre=None,  # cannot verify
        )
        summary = self.checker.check_claims(
            ["Sugar Free", "High Protein", "High Fibre", "Natural"],
            profile
        )
        assert summary.total_claims == 4
        assert summary.supported_count == 1
        assert summary.not_supported_count == 1
        assert summary.cannot_verify_count == 1
        assert summary.not_checkable_count == 1
        assert "1 of 4 claims supported" in summary.summary_sentence
        for r in summary.results:
            assert "differ by product category" in r.disclaimer
