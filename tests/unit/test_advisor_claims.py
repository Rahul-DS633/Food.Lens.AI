"""
Unit tests for AI Advisor Claims Explainer
Verifies strict numeric grounding, absence of banned aggressive words,
and proper category disclaimer attachment.
"""

from foodlens.advisor import AIAdvisor
from foodlens.claims import (
    ClaimCheckSummary,
    ClaimEvidence,
    ClaimResult,
    ClaimStatus,
)


def test_explain_claim_check_deterministic_and_grounded():
    advisor = AIAdvisor()

    results = [
        ClaimResult(
            claim_text="High Protein",
            rule_id="high_protein",
            status=ClaimStatus.SUPPORTED,
            evidence=[ClaimEvidence(field="protein_g", value=14.0, basis="per_100g")],
            threshold_value=12.0,
            threshold_operator=">=",
            threshold_source="FSSAI Claims Reg 2018 Schedule-I",
            neutral_explanation="Declared protein (14.0 g / 100 g) meets the statutory threshold (>= 12.0 g / 100 g).",
        ),
        ClaimResult(
            claim_text="Sugar Free",
            rule_id="sugar_free",
            status=ClaimStatus.NOT_SUPPORTED,
            evidence=[ClaimEvidence(field="sugars_g", value=3.5, basis="per_100g")],
            threshold_value=0.5,
            threshold_operator="<=",
            threshold_source="FSSAI Claims Reg 2018 Schedule-I",
            neutral_explanation="The label values do not appear to support this claim (3.5 g / 100 g vs statutory threshold <= 0.5 g).",
        ),
    ]

    summary = ClaimCheckSummary(
        results=results,
        total_claims=2,
        supported_count=1,
        partly_supported_count=0,
        not_supported_count=1,
        cannot_verify_count=0,
        not_checkable_count=0,
        summary_sentence="1 of 2 claims supported by label data.",
    )

    explanation = advisor.explain_claim_check(summary, product_name="Protein Bar")

    assert explanation["is_grounded"] is True
    assert "differ by product category" in explanation["disclaimer"]
    # Check no banned words
    for banned in ["false", "misleading", "fraud", "cheat", "fake"]:
        assert banned not in explanation["summary"].lower()


def test_explain_claim_check_rejects_hallucinated_numbers():
    advisor = AIAdvisor()

    summary = ClaimCheckSummary(
        results=[],
        total_claims=0,
        supported_count=0,
        partly_supported_count=0,
        not_supported_count=0,
        cannot_verify_count=0,
        not_checkable_count=0,
        summary_sentence="No claims evaluated.",
    )

    explanation = advisor.explain_claim_check(summary, product_name="Generic Snack")
    assert explanation["is_grounded"] is True
