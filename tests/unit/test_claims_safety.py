"""
Safety and Legal Neutrality Scanner for Claim Checker
Verifies that banned aggressive/defamatory words ('false', 'misleading', 'fraud', 'cheat', 'fake')
never appear in user-facing code, configs, explanations, or templates.
"""

from pathlib import Path
import re
import pytest
from foodlens.claims import ClaimChecker
from foodlens.nutrition import NutritionProfile, create_nutrient


BANNED_WORDS = ["false", "misleading", "fraud", "cheat", "fake", "deceptive"]


def test_banned_words_not_in_claims_config():
    config_path = Path("foodlens/config/claims.yaml")
    if not config_path.exists():
        pytest.fail("claims.yaml configuration not found")

    text = config_path.read_text(encoding="utf-8").lower()
    for word in BANNED_WORDS:
        # Check whole word
        match = re.search(r"\b" + re.escape(word) + r"\b", text)
        assert match is None, f"Banned word '{word}' found in foodlens/config/claims.yaml"


def test_banned_words_not_in_generated_explanations():
    checker = ClaimChecker()
    # Test across multiple non-supported or edge profiles
    bad_profile = NutritionProfile(
        basis="per_100g",
        serving_size_g=100.0,
        sugars_g=create_nutrient(50.0, "g", "per_100g"),
        fat_g=create_nutrient(30.0, "g", "per_100g"),
        protein_g=create_nutrient(1.0, "g", "per_100g"),
        fibre_g=create_nutrient(0.2, "g", "per_100g"),
        sodium_mg=create_nutrient(800.0, "mg", "per_100g"),
        trans_fat_g=create_nutrient(2.5, "g", "per_100g"),
    )

    claims_to_test = [
        "Sugar Free", "Low Sugar", "No Added Sugar", "High Protein", "Source of Protein",
        "High Fibre", "Fat Free", "Low Fat", "Zero Trans Fat", "Low Sodium",
        "100% Whole Wheat", "Multigrain", "No Maida", "100% Natural", "Healthy"
    ]

    summary = checker.check_claims(
        claims_to_test,
        bad_profile,
        ingredients_text="Maida, sugar, palm oil, artificial colors"
    )
    for res in summary.results:
        explanation = res.neutral_explanation.lower()
        for word in BANNED_WORDS:
            assert word not in explanation, (
                f"Banned word '{word}' found in explanation for claim '{res.claim_text}': {res.neutral_explanation}"
            )
        assert "differ by product category" in res.disclaimer.lower()
