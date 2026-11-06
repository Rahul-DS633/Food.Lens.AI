"""
Unit tests for foodlens/sugar_detector.py
Tests alias coverage, fuzzy matching on OCR typos, edge cases (sugarcane vinegar),
sweetener vs sugar distinctions, lactose ambiguity, sugar splitting heuristics,
label conflict cross-check, teaspoon rounding, and property monotonicity.
"""

import pytest
from hypothesis import given, strategies as st
from foodlens.sugar_detector import SugarDetector, SugarReport, SugarMatch


def test_all_sugar_classes_covered():
    detector = SugarDetector()
    text = (
        "Ingredients: Refined Wheat Flour, Sugar, Invert Syrup, Apple Juice Concentrate, "
        "Maltodextrin, Sucralose, Lactose, Salt."
    )
    report = detector.detect_sugars(text)

    assert report.status == "OK"
    classes_found = {m.sugar_class for m in report.matches}
    assert "sugars" in classes_found
    assert "syrups" in classes_found
    assert "concentrates" in classes_found
    assert "carb_fillers" in classes_found
    assert "non_sugar_sweeteners" in classes_found
    assert "ambiguous" in classes_found


def test_indian_sugar_synonyms():
    detector = SugarDetector()
    texts = [
        "Ingredients: Roasted Peanuts, Jaggery (Gur 35%), Cardamom.",
        "Ingredients: Sesame Seeds, Gud, Ghee.",
        "Ingredients: Wheat Flour, Liquid Glucose, Palm Oil, Cheeni.",
        "Ingredients: Khandsari, Cocoa Solids, Milk Fat.",
        "Ingredients: Roasted Chana, Shakar, Salt.",
    ]
    for text in texts:
        rep = detector.detect_sugars(text)
        assert rep.status == "OK"
        assert len(rep.distinct_sugar_names) >= 1
        assert any(m.sugar_class in ("sugars", "syrups") for m in rep.matches)


def test_fuzzy_ocr_typo_matching():
    detector = SugarDetector()
    # Typical OCR errors: 'dextroze', 'invertt syrup', 'glukose'
    text = "Ingredients: Wheat Flour, Dextroze, Invertt Syrup, Palm Oil, Glukose."
    rep = detector.detect_sugars(text)

    assert rep.status == "OK"
    fuzzy_matches = [m for m in rep.matches if m.match_type == "fuzzy"]
    assert len(fuzzy_matches) >= 2
    for fm in fuzzy_matches:
        assert fm.confidence < 1.0
        assert fm.confidence >= 0.80


def test_sugarcane_vinegar_not_counted_as_sugar():
    detector = SugarDetector()
    # Sugarcane vinegar is fermented acetic acid, not caloric sugar
    text1 = "Ingredients: Water, Sugarcane Vinegar, Salt, Spices."
    text2 = "Ingredients: Cane Vinegar, Mustard Seeds, Red Chili."
    text3 = "Ingredients: Sugar Cane Vinegar, Acidity Regulator (INS 260)."

    for text in (text1, text2, text3):
        rep = detector.detect_sugars(text)
        assert len(rep.distinct_sugar_names) == 0
        assert not any(m.sugar_class == "sugars" for m in rep.matches)


def test_sweeteners_not_counted_in_sugar_totals():
    detector = SugarDetector()
    text = "Ingredients: Water, Carbon Dioxide, Acidity Regulators (INS 330, 331), Aspartame, Acesulfame K, Sucralose."
    rep = detector.detect_sugars(text)

    # Sweeteners must be tracked in non_sugar_sweeteners
    assert len(rep.non_sugar_sweeteners) >= 2
    # But distinct_sugar_names must be empty
    assert len(rep.distinct_sugar_names) == 0
    assert all(m.is_added == "no" for m in rep.matches if m.sugar_class == "non_sugar_sweeteners")


def test_lactose_marked_ambiguous_never_added():
    detector = SugarDetector()
    text = "Ingredients: Skimmed Milk, Lactose, Whey Powder, Vegetable Oil."
    rep = detector.detect_sugars(text)

    ambiguous_matches = [m for m in rep.matches if m.sugar_class == "ambiguous"]
    assert len(ambiguous_matches) >= 1
    for m in ambiguous_matches:
        assert m.is_added == "ambiguous"
        assert m.is_added != "yes"


def test_carb_fillers_flagged_separately():
    detector = SugarDetector()
    text = "Ingredients: Pea Protein, Maltodextrin, Cocoa Powder, Corn Dextrin, Salt."
    rep = detector.detect_sugars(text)

    assert len(rep.carb_fillers) >= 2
    assert "maltodextrin" in [c.lower() for c in rep.carb_fillers]
    assert len(rep.distinct_sugar_names) == 0  # Fillers are not sugars


def test_sugar_splitting_heuristic():
    detector = SugarDetector()
    # 3 distinct sugar names -> sugar splitting flagged
    split_text = "Ingredients: Wheat Flour, Sugar, Invert Syrup, Liquid Glucose, Vegetable Fat, Salt."
    rep_split = detector.detect_sugars(split_text)
    assert rep_split.sugar_splitting is True
    assert len(rep_split.distinct_sugar_names) >= 3

    # Only 1 sugar name -> no sugar splitting
    single_text = "Ingredients: Wheat Flour, Sugar, Palm Oil, Salt."
    rep_single = detector.detect_sugars(single_text)
    assert rep_single.sugar_splitting is False


def test_sugars_in_top3_detection():
    detector = SugarDetector()
    # Position 2 -> in top 3
    top_text = "Ingredients: Wheat Flour, Sugar, Edible Vegetable Oil, Salt."
    rep_top = detector.detect_sugars(top_text)
    assert rep_top.sugars_in_top3 is True
    assert rep_top.first_sugar_position == 2

    # Sugar at position 4 -> NOT in top 3
    late_text = "Ingredients: Whole Oats, Almonds, Chia Seeds, Honey, Vanilla."
    rep_late = detector.detect_sugars(late_text)
    assert rep_late.sugars_in_top3 is False
    assert rep_late.first_sugar_position == 4


def test_label_conflict_zero_added_sugar_with_syrup():
    detector = SugarDetector()
    text = "Ingredients: Whole Wheat Flour, Invert Sugar Syrup, Vegetable Oil, Raising Agents."
    # Table declares 0g added sugar, but Invert Sugar is present
    rep = detector.detect_sugars(
        ingredients_text=text,
        added_sugar_g=0.0,
        total_sugars_g=5.0,
        portion_g=30.0
    )

    assert rep.label_conflict is True
    assert "0g added sugar" in (rep.label_conflict_reason or "").lower()
    assert "invert" in (rep.label_conflict_reason or "").lower()


def test_teaspoon_rounding_to_half_step():
    detector = SugarDetector()
    # 7.0g -> 7 / 4 = 1.75 -> 2.0 tsp
    rep1 = detector.detect_sugars("Sugar", added_sugar_g=7.0, portion_g=25.0)
    assert rep1.portion_teaspoons == 2.0
    assert rep1.teaspoon_basis == "added_sugar"

    # 6.0g -> 6 / 4 = 1.50 -> 1.5 tsp
    rep2 = detector.detect_sugars("Sugar", added_sugar_g=6.0, portion_g=25.0)
    assert rep2.portion_teaspoons == 1.5

    # 2.0g -> 2 / 4 = 0.50 -> 0.5 tsp
    rep3 = detector.detect_sugars("Sugar", added_sugar_g=2.0, portion_g=25.0)
    assert rep3.portion_teaspoons == 0.5

    # Fallback to total sugars if added sugar is None
    rep_fallback = detector.detect_sugars("Sugar", added_sugar_g=None, total_sugars_g=10.0, portion_g=50.0)
    assert rep_fallback.portion_teaspoons == 2.5
    assert rep_fallback.teaspoon_basis == "total_sugars"


def test_missing_or_unreadable_text_returns_unknown():
    detector = SugarDetector()
    rep_none = detector.detect_sugars(None)
    assert rep_none.status == "UNKNOWN"

    rep_empty = detector.detect_sugars("   ")
    assert rep_empty.status == "UNKNOWN"

    rep_low_conf = detector.detect_sugars("Wheat Flour, Sugar", ocr_confidence=0.45)
    assert rep_low_conf.status == "UNKNOWN"


# --- Property-Based Test (Hypothesis) ---

@given(st.lists(st.sampled_from(["Wheat Flour", "Sugar", "Palm Oil", "Invert Syrup", "Salt", "Maltodextrin", "Sucralose"]), min_size=1, max_size=10))
def test_matches_positions_are_monotonic(ingredients_list):
    detector = SugarDetector()
    text = ", ".join(ingredients_list)
    rep = detector.detect_sugars(text)

    positions = [m.position for m in rep.matches]
    # Invariant: Output match positions must be monotonically non-decreasing
    assert positions == sorted(positions)
