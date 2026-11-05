"""
Unit tests for foodlens/ingredients.py
"""

from foodlens.ingredients import IngredientEngine


def test_split_ingredients_nested_parentheses():
    engine = IngredientEngine()
    text = "Wheat Flour (68%), Sugar, Palm Oil, Raising Agents [503(ii), 500(ii)], Salt, Milk Solids, Emulsifier [322]."
    tokens = engine.split_ingredients_text(text)
    assert len(tokens) == 7
    assert tokens[0] == "Wheat Flour (68%)"
    assert tokens[3] == "Raising Agents [503(ii), 500(ii)]"
    assert tokens[6] == "Emulsifier [322]"


def test_ingredient_analysis_and_allergen_detection():
    engine = IngredientEngine()
    text = "Wheat Flour (68%), Sugar, Palm Oil, Milk Solids, Emulsifier (Soy Lecithin), Salt."
    result = engine.analyze(text)

    assert result.has_allergens is True
    assert "gluten" in result.detected_allergens or "wheat" in result.detected_allergens
    assert "milk" in result.detected_allergens
    assert "soy" in result.detected_allergens
    assert "Contains / May Contain:" in result.allergen_banner

    # Check INS 322 explanation
    res_ins = engine.analyze("Emulsifier [322], Acidity Regulator [330]")
    assert any(ing.category == "emulsifier" for ing in res_ins.ingredients)
    assert any(ing.category == "acidulant" for ing in res_ins.ingredients)


def test_allergen_free_safety_wording():
    engine = IngredientEngine()
    # Simple fruit salad or pure sugar water
    text = "Water, Sugar, Mango Pulp, Citric Acid."
    result = engine.analyze(text)

    assert result.has_allergens is False
    assert result.allergen_banner == "No allergen detected in the text we could read."
    assert "free" not in result.allergen_banner.lower()
