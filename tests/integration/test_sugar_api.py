"""
Integration tests for Sugar Detection API route handlers
Tests end-to-end detection logic directly with SQLite session.
"""

import pytest
from db.session import SessionLocal, init_db
from api.routes.sugar import analyze_hidden_sugars
from api.schemas import SugarAnalyzeRequest


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_sugar_analyze_route_with_product_id():
    db = SessionLocal()
    try:
        # Preseeded Product #1 = Parle-G (contains Wheat Flour, Sugar, Invert Sugar, etc.)
        req = SugarAnalyzeRequest(product_id=1, portion_g=25.0)
        resp = analyze_hidden_sugars(req, db=db)

        assert resp.status == "OK"
        assert len(resp.matches) >= 1
        assert "sugar" in [m.normalized_alias for m in resp.matches]
        assert resp.portion_teaspoons is not None
        assert resp.teaspoon_basis in ("added_sugar", "total_sugars")
        assert len(resp.ai_summary) > 0
    finally:
        db.close()


def test_sugar_analyze_route_with_custom_text():
    db = SessionLocal()
    try:
        custom_text = (
            "Ingredients: Rolled Oats, Jaggery (Gur), Invert Sugar, Liquid Glucose, "
            "Maltodextrin, Sucralose, Salt."
        )
        req = SugarAnalyzeRequest(
            ingredients_text=custom_text,
            added_sugar_g=12.0,
            portion_g=50.0
        )
        resp = analyze_hidden_sugars(req, db=db)

        assert resp.status == "OK"
        assert resp.sugar_splitting is True
        assert len(resp.distinct_sugar_names) >= 3
        assert "sucralose" in [s.lower() for s in resp.non_sugar_sweeteners]
        assert "maltodextrin" in [c.lower() for c in resp.carb_fillers]
        assert resp.portion_teaspoons == 3.0  # 12 / 4 = 3.0
    finally:
        db.close()

