"""
Integration Tests for Claims API Route (/api/claims/check)
"""

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from api.routes.claims import check_product_claims
from api.schemas import ClaimCheckRequest
from db.models import Ingredient, Nutrition, Product
from db.session import SessionLocal, init_db


@pytest.fixture
def setup_product():
    init_db()
    db: Session = SessionLocal()
    # Clean up old test products if any
    db.query(Product).filter(Product.barcode == "8901234567890").delete()
    db.commit()

    prod = Product(
        barcode="8901234567890",
        name="Apex High Protein Bar",
        brand="Apex Nutrition",
        category="general",
        serving_size_g=50.0,
        net_weight_g=100.0,
    )
    db.add(prod)
    db.commit()
    db.refresh(prod)

    nut = Nutrition(
        product_id=prod.id,
        basis="per_100g",
        energy_kcal=380.0,
        protein_g=18.0,
        carbs_g=40.0,
        sugars_g=0.3,
        added_sugar_g=0.0,
        fat_g=8.0,
        sat_fat_g=1.2,
        trans_fat_g=0.0,
        fibre_g=7.5,
        sodium_mg=95.0,
    )
    db.add(nut)

    ing1 = Ingredient(product_id=prod.id, position=1, name="Whole wheat flour")
    ing2 = Ingredient(product_id=prod.id, position=2, name="Whey protein concentrate")
    ing3 = Ingredient(product_id=prod.id, position=3, name="Almonds")
    db.add_all([ing1, ing2, ing3])
    db.commit()

    prod_id = prod.id
    db.close()

    yield prod_id

    # Teardown
    td_db: Session = SessionLocal()
    td_db.query(Ingredient).filter(Ingredient.product_id == prod_id).delete()
    td_db.query(Nutrition).filter(Nutrition.product_id == prod_id).delete()
    td_db.query(Product).filter(Product.id == prod_id).delete()
    td_db.commit()
    td_db.close()


def test_claims_check_endpoint(setup_product):
    prod_id = setup_product
    db: Session = SessionLocal()
    try:
        req = ClaimCheckRequest(
            product_id=prod_id,
            claims=["High Protein", "Sugar Free", "100% Whole Wheat", "100% Natural"]
        )

        resp = check_product_claims(req, db=db)

        assert resp.total_claims == 4
        assert resp.supported_count >= 3
        assert len(resp.results) == 4

        statuses = {r.claim_text: r.status for r in resp.results}
        assert statuses["High Protein"] == "SUPPORTED"
        assert statuses["Sugar Free"] == "SUPPORTED"
        assert statuses["100% Whole Wheat"] == "SUPPORTED"
        assert statuses["100% Natural"] == "NOT_CHECKABLE"

        assert resp.ai_summary is not None
        assert "differ by product category" in resp.ai_summary["disclaimer"]
    finally:
        db.close()


def test_claims_check_product_not_found():
    db: Session = SessionLocal()
    try:
        req = ClaimCheckRequest(product_id=999999, claims=["High Protein"])
        with pytest.raises(HTTPException) as exc_info:
            check_product_claims(req, db=db)
        assert exc_info.value.status_code == 404
    finally:
        db.close()
