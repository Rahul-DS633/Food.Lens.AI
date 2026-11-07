"""
Unit Tests for Report Auto-Checks, Consensus, and State Machine
Rules:
1. Pure Python deterministic checks.
2. Validates plausibility, subset rules, and OCR match scores.
3. Detects duplicate reports and computes consensus priority scores.
4. Enforces valid state-machine transitions.
"""

import pytest
from foodlens.report_checks import (
    validate_proposed_field,
    detect_duplicate_report,
    calculate_priority_score,
    validate_state_transition,
    ReportAutoCheckResult,
)


def test_plausibility_and_subset_checks_on_proposed_values():
    current_nutrients = {
        "energy_kcal": 250.0,
        "carbs_g": 30.0,
        "sugars_g": 10.0,
        "added_sugar_g": 5.0,
        "protein_g": 8.0,
        "fat_g": 10.0,
    }

    # Negative value is implausible
    res_neg = validate_proposed_field("protein_g", "-5.0", current_nutrients)
    assert res_neg.is_plausible is False
    assert any("negative" in f.lower() for f in res_neg.flags)

    # Added sugar > total sugar violates subset rule
    res_subset = validate_proposed_field("added_sugar_g", "20.0", current_nutrients)
    assert res_subset.is_plausible is False
    assert any("added sugar cannot exceed total sugars" in f.lower() for f in res_subset.flags)

    # Valid plausible adjustment
    res_valid = validate_proposed_field("protein_g", "12.0", current_nutrients)
    assert res_valid.is_plausible is True
    assert len(res_valid.flags) == 0


def test_duplicate_detection_clusters_matching_reports():
    existing_reports = [
        {"field": "protein_g", "proposed_value": "12.0", "status": "pending", "id": 101},
        {"field": "name", "proposed_value": "Oat Krunch", "status": "pending", "id": 102},
    ]

    # Exact match on field and value
    dup1 = detect_duplicate_report("protein_g", "12.0", existing_reports)
    assert dup1 is not None
    assert dup1["id"] == 101

    # Numeric floating tolerance match (12.0 vs 12)
    dup2 = detect_duplicate_report("protein_g", "12", existing_reports)
    assert dup2 is not None
    assert dup2["id"] == 101

    # Different value is not duplicate
    dup3 = detect_duplicate_report("protein_g", "15.0", existing_reports)
    assert dup3 is None

    # Different field is not duplicate
    dup4 = detect_duplicate_report("energy_kcal", "250", existing_reports)
    assert dup4 is None


def test_consensus_scoring_raises_priority():
    # Base score
    score_base = calculate_priority_score(consensus_count=1, ocr_match_score=0.0, has_validation_flags=False)
    assert score_base == 1.0

    # High consensus + high OCR match raises priority
    score_high = calculate_priority_score(consensus_count=3, ocr_match_score=0.9, has_validation_flags=False)
    assert score_high > score_base
    assert score_high >= 4.0

    # Validation flags lower priority score
    score_penalized = calculate_priority_score(consensus_count=3, ocr_match_score=0.9, has_validation_flags=True)
    assert score_penalized < score_high


def test_state_machine_transitions():
    # Allowed transitions from 'pending'
    assert validate_state_transition("pending", "approved") is True
    assert validate_state_transition("pending", "rejected") is True
    assert validate_state_transition("pending", "needs_info") is True
    assert validate_state_transition("pending", "duplicate") is True

    # Allowed transition from 'needs_info' to 'approved'
    assert validate_state_transition("needs_info", "approved") is True

    # Terminal or illegal transitions
    with pytest.raises(ValueError):
        validate_state_transition("approved", "pending")

    with pytest.raises(ValueError):
        validate_state_transition("rejected", "approved")

    with pytest.raises(ValueError):
        validate_state_transition("duplicate", "pending")
