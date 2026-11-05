"""
Integration tests for FoodLens API route handlers
Tests end-to-end route logic directly with SQLite session.
"""

from db.session import SessionLocal
from api.routes.scan import scan_barcode
from api.routes.nutrition import calculate_nutritional_portion
from api.routes.quest import get_quest_progress, submit_minigame_attempt
from api.routes.compare import compare_products
from api.schemas import (
    BarcodeScanRequest, CalculatePortionRequest, CompareRequest, QuestAttemptRequest
)


def test_scan_barcode_route_preseeded():
    db = SessionLocal()
    try:
        req = BarcodeScanRequest(barcode="8901719101052")
        resp = scan_barcode(payload=req, file=None, db=db)
        assert resp.found is True
        assert resp.product["brand"] == "Parle"
        assert resp.score["score"] is not None
        assert resp.xp_awarded >= 10
    finally:
        db.close()


def test_calculate_portion_route():
    db = SessionLocal()
    try:
        req = CalculatePortionRequest(
            product_id=1,
            portion_type="serving",
            servings=1.0
        )
        resp = calculate_nutritional_portion(req, db=db)
        assert resp["status"] == "success"
        assert "scaled_profile" in resp
        assert "sugar_teaspoons" in resp
    finally:
        db.close()


def test_compare_products_route():
    db = SessionLocal()
    try:
        req = CompareRequest(product_ids=[1, 2])
        resp = compare_products(req, db=db)
        assert resp["status"] == "success"
        assert resp["compared_count"] == 2
        assert resp["xp_awarded"] >= 10
    finally:
        db.close()


def test_quest_progress_and_attempt_routes():
    db = SessionLocal()
    try:
        prog = get_quest_progress(user_id=1, db=db)
        assert "xp" in prog
        assert "level" in prog
        assert "badges" in prog

        attempt_req = QuestAttemptRequest(
            user_id=1,
            game_type="guess_sugar",
            actual_value=25.0,
            user_guess=24.5
        )
        res = submit_minigame_attempt(attempt_req, db=db)
        assert res["status"] == "success"
        assert res["xp_awarded"] == 25
        assert "Bullseye" in res["message"]
    finally:
        db.close()
