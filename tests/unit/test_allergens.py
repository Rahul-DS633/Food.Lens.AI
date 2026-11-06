"""
Unit tests for foodlens/allergens.py
Deterministic allergen cross-checking, regional synonym resolution,
precautionary trace detection, and strict safety wording rules.
"""

import pytest
from foodlens.allergens import AllergenEngine, AllergenStatus


def test_milk_synonyms_detection():
    engine = AllergenEngine()
    user_allergies = ["milk"]

    # Ghee, paneer, whey, casein, milk solids
    texts = [
        "Ingredients: Wheat Flour, Sugar, Pure Cow Ghee, Cardamom.",
        "Ingredients: Paneer (Cottage Cheese), Tomato Paste, Spices.",
        "Ingredients: Whey Protein Concentrate, Cocoa, Stevia.",
        "Ingredients: Potato Flakes, Edible Vegetable Oil, Milk Solids, Salt.",
        "Ingredients: Refined Wheat Flour, Butter, Sugar, Casein.",
        "Ingredients: Mawa, Sugar, Pistachio.",
    ]
    for text in texts:
        res = engine.check_allergens(ingredients_text=text, user_allergies=user_allergies)
        assert res.overall_status == AllergenStatus.CONTAINS_YOUR_ALLERGEN
        assert any(item.allergen == "milk" and item.status == AllergenStatus.CONTAINS_YOUR_ALLERGEN for item in res.allergen_results)


def test_wheat_gluten_synonyms_detection():
    engine = AllergenEngine()
    user_allergies = ["wheat_gluten"]

    texts = [
        "Ingredients: Atta (Whole Wheat Flour 72%), Sugar, Yeast, Salt.",
        "Ingredients: Maida, Vegetable Fat, Invert Syrup, Raising Agents.",
        "Ingredients: Suji, Vegetable Oil, Mustard Seeds, Curry Leaves.",
        "Ingredients: Sooji Rava, Salt, Cashew Nuts.",
        "Ingredients: Semolina, Water.",
        "Ingredients: Malt Extract, Barley, Cocoa Powder.",
    ]
    for text in texts:
        res = engine.check_allergens(ingredients_text=text, user_allergies=user_allergies)
        assert res.overall_status == AllergenStatus.CONTAINS_YOUR_ALLERGEN
        assert any(item.allergen == "wheat_gluten" for item in res.allergen_results)


def test_peanut_and_regional_names():
    engine = AllergenEngine()
    user_allergies = ["peanut"]

    texts = [
        "Ingredients: Roasted Groundnuts, Salt, Spices.",
        "Ingredients: Moongphali Dana, Palm Oil, Black Salt.",
        "Ingredients: Arachis Oil, Potatoes, Salt.",
        "Ingredients: Peanuts (45%), Sugar, Glucose Syrup.",
    ]
    for text in texts:
        res = engine.check_allergens(ingredients_text=text, user_allergies=user_allergies)
        assert res.overall_status == AllergenStatus.CONTAINS_YOUR_ALLERGEN


def test_soy_and_ins_codes():
    engine = AllergenEngine()
    user_allergies = ["soy"]

    texts = [
        "Ingredients: Wheat Flour, Sugar, Emulsifier (Soy Lecithin).",
        "Ingredients: Soya Chunks, Defatted Soya Flour.",
        "Ingredients: Refined Palm Oil, Emulsifier [INS 322].",
        "Ingredients: Chocolate, Sugar, Emulsifier (E322).",
    ]
    for text in texts:
        res = engine.check_allergens(ingredients_text=text, user_allergies=user_allergies)
        assert res.overall_status == AllergenStatus.CONTAINS_YOUR_ALLERGEN


def test_tree_nuts_and_hindi_names():
    engine = AllergenEngine()
    user_allergies = ["tree_nuts"]

    texts = [
        "Ingredients: Kaju, Sugar, Silver Foil.",
        "Ingredients: Roasted Badam, Salt.",
        "Ingredients: Akhrot Kernels, Honey.",
        "Ingredients: Pista, Milk, Saffron.",
        "Ingredients: Cashew nuts, Almonds, Hazelnuts.",
    ]
    for text in texts:
        res = engine.check_allergens(ingredients_text=text, user_allergies=user_allergies)
        assert res.overall_status == AllergenStatus.CONTAINS_YOUR_ALLERGEN


def test_mustard_sesame_egg_fish_shellfish():
    engine = AllergenEngine()
    
    # Mustard
    res_m = engine.check_allergens("Ingredients: Sarson Ka Tel, Mango, Salt.", ["mustard"])
    assert res_m.overall_status == AllergenStatus.CONTAINS_YOUR_ALLERGEN

    # Sesame
    res_s = engine.check_allergens("Ingredients: Til, Jaggery, Cardamom.", ["sesame"])
    assert res_s.overall_status == AllergenStatus.CONTAINS_YOUR_ALLERGEN

    # Egg
    res_e = engine.check_allergens("Ingredients: Flour, Sugar, Anda Powder.", ["egg"])
    assert res_e.overall_status == AllergenStatus.CONTAINS_YOUR_ALLERGEN

    # Fish
    res_f = engine.check_allergens("Ingredients: Machhli, Tomato, Oil, Spices.", ["fish"])
    assert res_f.overall_status == AllergenStatus.CONTAINS_YOUR_ALLERGEN

    # Shellfish
    res_sh = engine.check_allergens("Ingredients: Dried Jhinga, Salt, Chili.", ["shellfish"])
    assert res_sh.overall_status == AllergenStatus.CONTAINS_YOUR_ALLERGEN


def test_may_contain_traces_distinction():
    engine = AllergenEngine()
    user_allergies = ["peanut", "tree_nuts"]

    # Peanut is in ingredients, tree nuts is in may contain
    text = "Ingredients: Wheat Flour, Sugar, Groundnut Oil. May contain traces of almonds and cashew nuts."
    res = engine.check_allergens(ingredients_text=text, user_allergies=user_allergies)

    p_check = next(r for r in res.allergen_results if r.allergen == "peanut")
    tn_check = next(r for r in res.allergen_results if r.allergen == "tree_nuts")

    assert p_check.status == AllergenStatus.CONTAINS_YOUR_ALLERGEN
    assert tn_check.status == AllergenStatus.MAY_CONTAIN_TRACES
    # Contains overrides may contain traces for overall status
    assert res.overall_status == AllergenStatus.CONTAINS_YOUR_ALLERGEN

    # Solely precautionary trace case
    text_trace_only = "Ingredients: Corn Flour, Sugar, Salt. Processed in a facility that also handles peanuts."
    res_trace = engine.check_allergens(ingredients_text=text_trace_only, user_allergies=["peanut"])
    assert res_trace.overall_status == AllergenStatus.MAY_CONTAIN_TRACES


def test_missing_or_low_confidence_yields_unknown():
    engine = AllergenEngine()
    user_allergies = ["milk", "peanut"]

    # Missing text
    res_none = engine.check_allergens(ingredients_text="", user_allergies=user_allergies)
    assert res_none.overall_status == AllergenStatus.UNKNOWN
    assert "Verify on the pack" in res_none.banner_text

    # Low OCR confidence (< 0.60)
    res_low_conf = engine.check_allergens(
        ingredients_text="Wheat Flour, Sugar, Edible Oil",
        user_allergies=user_allergies,
        ocr_confidence=0.45
    )
    assert res_low_conf.overall_status == AllergenStatus.UNKNOWN
    assert "Verify on the pack" in res_low_conf.banner_text


def test_no_allergen_detected_wording():
    engine = AllergenEngine()
    user_allergies = ["peanut", "fish"]
    text = "Ingredients: Water, Sugar, Mango Pulp, Citric Acid, Ascorbic Acid."

    res = engine.check_allergens(ingredients_text=text, user_allergies=user_allergies, ocr_confidence=0.95)
    assert res.overall_status == AllergenStatus.NONE_DETECTED_IN_READABLE_TEXT
    assert "safe" not in res.banner_text.lower()
    assert "allergen-free" not in res.banner_text.lower()
    assert "Verify on the pack" in res.banner_text


def test_custom_allergen_text():
    engine = AllergenEngine()
    text = "Ingredients: Noodles (Wheat Flour, Palm Oil), Seasoning (Salt, Monosodium Glutamate [INS 621], Garlic)."
    res = engine.check_allergens(
        ingredients_text=text,
        user_allergies=[],
        custom_allergens=["Monosodium Glutamate", "MSG"]
    )
    assert res.overall_status == AllergenStatus.CONTAINS_YOUR_ALLERGEN
    assert any("custom:" in r.allergen for r in res.allergen_results)
