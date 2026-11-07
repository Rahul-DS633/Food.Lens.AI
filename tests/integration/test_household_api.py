"""
Integration Tests for Household & Family Profiles API
Rules:
1. CRUD operations for Household and Members.
2. 8-member limit enforcement.
3. Cascade delete of members on household deletion.
4. Export household data contains all members.
5. POST /api/family/check runs multi-member checks.
"""

import pytest
from db.session import SessionLocal, init_db, export_household_data, delete_household_data
from db.models import Household, HouseholdMember, Product
from api.routes.household import (
    create_or_get_household,
    add_household_member,
    check_family_food_fit,
)
from api.schemas import HouseholdMemberCreate, FamilyCheckRequest


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    db = SessionLocal()
    try:
        db.query(HouseholdMember).delete()
        db.query(Household).delete()
        db.commit()
    finally:
        db.close()


def test_household_crud_and_cascade_delete():
    db = SessionLocal()
    try:
        user_id = 1
        # 1. Create or get household
        hh = create_or_get_household(user_id=user_id, db=db)
        assert hh.owner_user_id == user_id

        # 2. Add members
        m1_req = HouseholdMemberCreate(
            display_name="Kavita",
            emoji_avatar="👩",
            age=34,
            weight_kg=60.0,
            allergies=["peanut"],
            dietary_prefs=["vegetarian"],
            consent_by_owner=True,
        )
        m1 = add_household_member(user_id=user_id, req=m1_req, db=db)
        assert m1.display_name == "Kavita"
        assert m1.is_minor is False

        m2_req = HouseholdMemberCreate(
            display_name="Ananya",
            emoji_avatar="👧",
            age=8,
            weight_kg=24.0,
            allergies=["milk"],
            dietary_prefs=["vegetarian"],
            consent_by_owner=True,
        )
        m2 = add_household_member(user_id=user_id, req=m2_req, db=db)
        assert m2.display_name == "Ananya"
        assert m2.is_minor is True

        # 3. Export household data
        exp = export_household_data(user_id=user_id, db=db)
        assert exp is not None
        assert exp["member_count"] == 2
        assert any(m["display_name"] == "Ananya" for m in exp["members"])

        # 4. Check family food fit route
        prod = db.query(Product).first()
        fit_req = FamilyCheckRequest(
            product_id=prod.id,
            member_ids=[m1.id, m2.id],
            portions={m1.id: 50.0, m2.id: 25.0},
        )
        fit_resp = check_family_food_fit(fit_req, db=db)
        assert fit_resp.worst_allergen_status in ["CONTAINS_YOUR_ALLERGEN", "MAY_CONTAIN_TRACES", "UNKNOWN", "NONE_DETECTED_IN_READABLE_TEXT"]
        assert len(fit_resp.members_evaluated) == 2

        # 5. Cascade delete
        deleted = delete_household_data(user_id=user_id, db=db)
        assert deleted is True

        # Assert members are gone
        members_remaining = db.query(HouseholdMember).filter(HouseholdMember.household_id == hh.id).count()
        assert members_remaining == 0
    finally:
        db.close()
