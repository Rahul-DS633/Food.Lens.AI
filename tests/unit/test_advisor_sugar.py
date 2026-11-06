"""
Unit tests for AI Advisor Hidden Sugar explanation extension in foodlens/advisor.py
Validates strict number grounding, neutral wording, and refusal of disease claims.
"""

import pytest
from foodlens.sugar_detector import SugarDetector
from foodlens.advisor import AIAdvisor


def test_sugar_explanation_strictly_grounded():
    advisor = AIAdvisor()
    detector = SugarDetector()
    text = "Ingredients: Refined Wheat Flour, Sugar, Invert Syrup, Palm Oil, Salt."
    report = detector.detect_sugars(text, added_sugar_g=8.0, portion_g=25.0)

    payload = {
        "product_name": "Cream Biscuit",
        "sugar_report": report.to_dict(),
    }

    explanation = advisor.generate_sugar_explanation(payload)

    # 1. Must be marked grounded
    assert explanation["is_grounded"] is True
    # 2. Key numbers from report must be verified (e.g. 2.0 tsp, 2 sugar types, position 2)
    assert len(explanation["flagged_numbers"]) == 0
    # 3. Refusal rule: No disease diagnosis or cure claims
    lowered = explanation["summary"].lower()
    assert "diabetes" not in lowered
    assert "cancer" not in lowered
    assert "toxic" not in lowered
    assert "unhealthy" not in lowered


def test_sugar_explanation_detects_ungrounded_hallucinations():
    advisor = AIAdvisor()
    detector = SugarDetector()
    report = detector.detect_sugars("Sugar", added_sugar_g=4.0, portion_g=25.0)
    payload = {
        "product_name": "Sweet Snack",
        "sugar_report": report.to_dict(),
    }

    fake_text = "This product contains 999.0 grams of hidden sucrose and 88.0 spoons."
    is_grounded, valid, flagged = advisor.verify_grounding(fake_text, payload)

    assert is_grounded is False
    assert 999.0 in flagged
    assert 88.0 in flagged
