"""
Integration tests for User Profile and Personal Fit API route handlers
Tests end-to-end route logic directly with SQLite session.
"""

import pytest
from fastapi import HTTPException
from db.session import SessionLocal, init_db
from api.routes.profile import save_user_profile, get_profile, export_profile, delete_profile
from api.routes.personal_fit import calculate_personal_fit
from api.schemas import UserProfileCreate, PersonalFitRequest


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_create_and_get_user_profile_route():
    db = SessionLocal()
    try:
        payload = UserProfileCreate(
            user_id=99,
            name="Arjun Sharma",
            age=28,
            weight_kg=72.0,
            allergies=["milk", "peanut"],
            custom_allergens="Preservative 220",
            language="en",
            consent_given=True,
            parental_consent_given=False,
        )

        # 1. Create Profile
        resp = save_user_profile(payload, db=db)
        assert resp.name == "Arjun Sharma"
        assert resp.age == 28
        assert resp.weight_kg == 72.0
        assert "milk" in resp.allergies
        assert resp.consent_given is True

        # 2. Get Profile
        resp_get = get_profile(user_id=99, db=db)
        assert resp_get.name == "Arjun Sharma"
    finally:
        db.close()


def test_consent_given_is_mandatory():
    db = SessionLocal()
    try:
        payload = UserProfileCreate(
            user_id=100,
            name="No Consent User",
            age=25,
            allergies=[],
            consent_given=False,
        )
        with pytest.raises(HTTPException) as exc_info:
            save_user_profile(payload, db=db)
        assert exc_info.value.status_code == 400
        assert "Consent to process dietary preferences is required" in str(exc_info.value.detail)
    finally:
        db.close()


def test_under_18_requires_parental_consent():
    db = SessionLocal()
    try:
        payload_no_parent = UserProfileCreate(
            user_id=101,
            name="Young Teen",
            age=14,
            allergies=["peanut"],
            consent_given=True,
            parental_consent_given=False,
        )
        with pytest.raises(HTTPException) as exc_info:
            save_user_profile(payload_no_parent, db=db)
        assert exc_info.value.status_code == 400
        assert "parental" in str(exc_info.value.detail).lower()

        # With parental consent it succeeds
        payload_parent = UserProfileCreate(
            user_id=101,
            name="Young Teen",
            age=14,
            allergies=["peanut"],
            consent_given=True,
            parental_consent_given=True,
        )
        resp_ok = save_user_profile(payload_parent, db=db)
        assert resp_ok.parental_consent_given is True
    finally:
        db.close()


def test_export_and_delete_user_data_routes():
    db = SessionLocal()
    try:
        # Setup user
        save_user_profile(UserProfileCreate(
            user_id=102,
            name="Export Delete User",
            age=35,
            allergies=["wheat_gluten"],
            consent_given=True,
        ), db=db)

        # Export
        exp_data = export_profile(user_id=102, db=db)
        assert exp_data["user_id"] == 102
        assert exp_data["profile"]["name"] == "Export Delete User"

        # Delete (Right to erasure)
        del_resp = delete_profile(user_id=102, db=db)
        assert del_resp["status"] == "success"

        # Check profile is gone
        with pytest.raises(HTTPException) as exc_info:
            get_profile(user_id=102, db=db)
        assert exc_info.value.status_code == 404
    finally:
        db.close()


def test_personal_fit_route_endpoint():
    db = SessionLocal()
    try:
        # Using preseeded product (id 1 = Parle-G)
        fit_req = PersonalFitRequest(
            product_id=1,
            portion_type="serving",
            profile_override=UserProfileCreate(
                name="Guest Visitor",
                age=27,
                weight_kg=68.0,
                allergies=["peanut"],
                custom_allergens="",
                language="en",
                consent_given=True,
            )
        )
        resp = calculate_personal_fit(fit_req, db=db)
        assert resp.verdict is not None
        assert resp.allergen_check is not None
        assert len(resp.nutrient_flags) > 0
        assert "General information, not medical advice" in resp.disclaimer
        assert resp.ai_explanation is not None
    finally:
        db.close()
