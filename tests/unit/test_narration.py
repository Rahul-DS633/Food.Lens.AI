"""
Unit & Snapshot Tests for Hindi and English Read-Aloud Audio Narration
Rules:
1. Deterministic spoken script from validated JSON (no LLM).
2. Order: Allergen alert first -> Product name -> Portion basis -> Key numbers -> Flags -> Closing disclaimer.
3. Every number in spoken script must exist in input JSON.
4. Banned words ('safe', 'allergen-free', 'सुरक्षित', 'एलर्जी-मुक्त') strictly forbidden.
5. Speech-friendly units: g -> ग्राम, mg -> मिलीग्राम, kcal -> किलोकैलोरी, tsp -> चम्मच.
6. Length under 45 seconds (approx < 95 words).
7. Zero personal names or avatars in scripts.
8. Complete key parity between i18n/en.json and i18n/hi.json.
"""

import json
from pathlib import Path
import re
import pytest

from foodlens.narration import generate_narration_script, NarrationMode


I18N_DIR = Path(__file__).resolve().parent.parent.parent / "i18n"


@pytest.fixture
def sample_product_dict():
    return {
        "name": "Parle-G Gold Biscuits",
        "portion_grams": 25.0,
        "portion_basis": "per_serving",
        "energy_kcal": 110.0,
        "sugars_g": 6.5,
        "sugar_teaspoons": 1.5,
        "protein_g": 1.8,
        "fat_g": 3.2,
        "sodium_mg": 75.0,
        "has_allergen_alert": True,
        "allergen_text": "Contains milk and wheat.",
        "notable_flags": ["Added sugar contributes over 20% of calories."],
    }


def test_i18n_keys_parity_between_en_and_hi():
    en_path = I18N_DIR / "en.json"
    hi_path = I18N_DIR / "hi.json"

    assert en_path.exists(), "i18n/en.json must exist"
    assert hi_path.exists(), "i18n/hi.json must exist"

    with open(en_path, "r", encoding="utf-8") as f:
        en_data = json.load(f)
    with open(hi_path, "r", encoding="utf-8") as f:
        hi_data = json.load(f)

    # Check key parity
    en_keys = set(en_data.keys())
    hi_keys = set(hi_data.keys())

    missing_in_hi = en_keys - hi_keys
    missing_in_en = hi_keys - en_keys

    assert not missing_in_hi, f"Keys in en.json missing in hi.json: {missing_in_hi}"
    assert not missing_in_en, f"Keys in hi.json missing in en.json: {missing_in_en}"


def test_narration_order_allergen_alert_first(sample_product_dict):
    for lang in ("en", "hi"):
        script = generate_narration_script(sample_product_dict, language=lang, mode=NarrationMode.DETAILED)
        sentences = [s.strip() for s in re.split(r"[.।]", script.text) if s.strip()]
        assert len(sentences) >= 3

        # First sentence must mention allergen alert
        first_sentence = sentences[0].lower()
        if lang == "en":
            assert "allergen" in first_sentence or "contains" in first_sentence
        else:
            assert "एलर्जी" in first_sentence or "शामिल" in first_sentence


def test_narration_numbers_grounded_in_input(sample_product_dict):
    # Test that every number in English narration exists in the input dictionary
    script_en = generate_narration_script(sample_product_dict, language="en", mode=NarrationMode.DETAILED)
    found_numbers = [float(n) for n in re.findall(r"\b\d+(?:\.\d+)?\b", script_en.text)]

    allowed_numbers = {
        float(v) for k, v in sample_product_dict.items() if isinstance(v, (int, float))
    }
    # Also 20 from notable flags
    allowed_numbers.add(20.0)

    for num in found_numbers:
        assert num in allowed_numbers, f"Ungrounded number {num} spoken in narration script!"


def test_banned_words_absent_in_en_and_hi(sample_product_dict):
    for lang in ("en", "hi"):
        script = generate_narration_script(sample_product_dict, language=lang, mode=NarrationMode.DETAILED)
        text_lower = script.text.lower()
        
        # Banned safety claims
        assert "allergen-free" not in text_lower
        assert "safe for everyone" not in text_lower
        assert "completely safe" not in text_lower
        assert "सुरक्षित" not in text_lower
        assert "एलर्जी-मुक्त" not in text_lower


def test_no_personal_names_in_narration(sample_product_dict):
    # Personal names like "Rahul", "Aarav", "Pooja" should never be embedded in the narration script
    sample_with_names = dict(sample_product_dict)
    sample_with_names["user_name"] = "Rahul"
    sample_with_names["family_member"] = "Aarav"

    script = generate_narration_script(sample_with_names, language="en", mode=NarrationMode.DETAILED)
    assert "Rahul" not in script.text
    assert "Aarav" not in script.text


def test_script_length_under_limit(sample_product_dict):
    for lang in ("en", "hi"):
        script_det = generate_narration_script(sample_product_dict, language=lang, mode=NarrationMode.DETAILED)
        words_det = script_det.text.split()
        assert len(words_det) <= 95, f"Detailed script exceeds 95 words ({len(words_det)} words)"

        script_short = generate_narration_script(sample_product_dict, language=lang, mode=NarrationMode.SHORT)
        words_short = script_short.text.split()
        assert len(words_short) <= 50, f"Short script exceeds 50 words ({len(words_short)} words)"


def test_speech_friendly_units_en_and_hi(sample_product_dict):
    script_en = generate_narration_script(sample_product_dict, language="en", mode=NarrationMode.DETAILED)
    assert "calories" in script_en.text.lower() or "kcal" not in script_en.text
    assert "teaspoons" in script_en.text.lower()
    assert "grams" in script_en.text.lower()

    script_hi = generate_narration_script(sample_product_dict, language="hi", mode=NarrationMode.DETAILED)
    assert "किलोकैलोरी" in script_hi.text or "कैलोरी" in script_hi.text
    assert "चम्मच" in script_hi.text
    assert "ग्राम" in script_hi.text
