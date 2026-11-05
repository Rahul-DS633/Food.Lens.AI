"""
Unit tests for foodlens/advisor.py
Validates grounding post-check, basis citation, and number verification.
"""

from foodlens.nutrition import NutritionProfile, create_nutrient
from foodlens.advisor import AIAdvisor


def test_advisor_grounding_post_check():
    advisor = AIAdvisor()
    profile = NutritionProfile(
        basis="per_100g",
        energy_kcal=create_nutrient(420.0, "kcal"),
        protein_g=create_nutrient(7.5, "g"),
        sugars_g=create_nutrient(24.0, "g"),
        fat_g=create_nutrient(12.0, "g"),
        sodium_mg=create_nutrient(300.0, "mg"),
        serving_size_g=25.0,
        net_weight_g=100.0,
    )
    payload = advisor.build_input_payload(
        product_name="Glucose Biscuit",
        brand="Britannia",
        category="biscuits",
        profile=profile,
        portion_basis="per_100g"
    )

    explanation = advisor.generate_explanation(payload)

    # Explanation must be grounded
    assert explanation.is_grounded is True
    assert len(explanation.flagged_numbers) == 0
    assert 420.0 in explanation.evidence_numbers_used or 7.5 in explanation.evidence_numbers_used
    assert "per_100g" in explanation.summary
    assert "per_100g" in explanation.protein
    assert "per_100g" in explanation.sugar


def test_advisor_detects_ungrounded_hallucinated_numbers():
    advisor = AIAdvisor()
    payload = {
        "product_name": "Test Drink",
        "nutrients": {
            "sugars_g": {"value": 10.0}
        }
    }
    # Text mentions 999.0 which is nowhere in payload
    fake_text = "This drink contains 999.0 mg of caffeine."
    is_grounded, valid, flagged = advisor.verify_grounding(fake_text, payload)
    assert is_grounded is False
    assert 999.0 in flagged
