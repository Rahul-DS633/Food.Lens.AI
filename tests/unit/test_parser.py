"""
Unit tests for foodlens/parser.py and OCR text extraction.
Validates exact-match extraction on messy label strings, comma decimals, and basis detection.
"""

from foodlens.parser import parse_ocr_text, clean_text_line, detect_basis_and_serving


def test_clean_text_line():
    assert clean_text_line("Energy: 450 kcal - approx") == "energy 450 kcal approx"
    assert clean_text_line("Total  Carbohydrates:   65.0g") == "total carbohydrates 65.0g"


def test_detect_basis_and_serving():
    text1 = "Nutrition Facts Per 100g of product Serving Size: 25g"
    basis, serving, is_bev = detect_basis_and_serving(text1)
    assert basis == "per_100g"
    assert serving == 25.0
    assert not is_bev

    text2 = "Nutritional Information per 100 ml Beverage"
    basis, serving, is_bev = detect_basis_and_serving(text2)
    assert basis == "per_100ml"
    assert is_bev is True


def test_parse_typical_indian_biscuit_label():
    label_lines = [
        "NUTRITIONAL INFORMATION",
        "Approximate Values Per 100g",
        "Energy: 460 kcal",
        "Protein: 7.0 g",
        "Carbohydrate: 72.0 g",
        "Total Sugars: 24.5 g",
        "Added Sugars: 22.0 g",
        "Total Fat: 16.0 g",
        "Saturated Fatty Acids: 7.5 g",
        "Trans Fatty Acids: 0.05 g",
        "Dietary Fibre: 2.5 g",
        "Sodium: 320 mg",
    ]
    confidences = [0.95] * len(label_lines)

    profile, details = parse_ocr_text(label_lines, confidences)

    assert profile.basis == "per_100g"
    assert profile.energy_kcal.value == 460.0
    assert profile.protein_g.value == 7.0
    assert profile.carbs_g.value == 72.0
    assert profile.sugars_g.value == 24.5
    assert profile.added_sugar_g.value == 22.0
    assert profile.fat_g.value == 16.0
    assert profile.sat_fat_g.value == 7.5
    assert profile.trans_fat_g.value == 0.05
    assert profile.fibre_g.value == 2.5
    assert profile.sodium_mg.value == 320.0
    assert len(details["low_confidence_fields"]) == 0


def test_parse_messy_text_comma_decimals_and_kj():
    # Real-world messy OCR with comma decimals and energy in kJ
    label_lines = [
        "Valeur nutritive / per 100g",
        "Energie 1750 kJ",
        "Proteines: 6,8 g",
        "Glucides / Carbohydrate 65,4 g",
        "dont sucres / of which sugars 18,2 g",
        "Lipides / Total Fat: 14,0 g",
        "Acides gras satures: 6,2 g",
        "Sel / Salt: 1,2 g",  # Salt instead of sodium
    ]
    profile, details = parse_ocr_text(label_lines)

    # 1750 kJ / 4.184 = 418.26 kcal
    assert profile.energy_kcal.value == 418.26
    assert profile.protein_g.value == 6.8
    assert profile.carbs_g.value == 65.4
    assert profile.sugars_g.value == 18.2
    assert profile.fat_g.value == 14.0
    assert profile.sat_fat_g.value == 6.2
    # Salt 1.2g -> Sodium (1.2 / 2.5 * 1000) = 480.0 mg
    assert profile.sodium_mg.value == 480.0
    # Missing fields must remain None
    assert profile.added_sugar_g is None
    assert profile.trans_fat_g is None
    assert profile.fibre_g is None

