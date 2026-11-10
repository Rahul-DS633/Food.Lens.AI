"""
Integration tests for FoodLens Authentication & Access API routes.
Tests route handlers directly with SQLite sessions.
"""

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.schemas import (
    UserLoginRequest,
    AdminLoginRequest,
    UserRegisterRequest,
)
from api.routes.auth import (
    register_account,
    login_user,
    login_admin,
    list_available_profiles,
)
from db.models import Base


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


def test_api_register_and_login_flow(db_session):
    # 1. Register new user
    reg_req = UserRegisterRequest(
        username="priya_fit",
        password="priyapassword",
        display_name="Priya Singh",
        email="priya@example.com",
        age=27,
        allergies=["gluten", "milk"],
        custom_allergens="preservative 211",
        consent_given=True,
        parental_consent_given=False,
        language="en"
    )
    res_reg = register_account(reg_req, db=db_session)
    assert res_reg.success is True
    assert res_reg.user is not None
    assert res_reg.user.username == "priya_fit"
    assert res_reg.user.display_name == "Priya Singh"
    assert res_reg.user.xp == 25

    # 2. Login with registered user
    login_req = UserLoginRequest(
        identifier="priya_fit",
        password="priyapassword"
    )
    res_login = login_user(login_req, db=db_session)
    assert res_login.success is True
    assert res_login.user.username == "priya_fit"

    # 3. Login with wrong password
    bad_login = UserLoginRequest(
        identifier="priya_fit",
        password="wrongpassword"
    )
    with pytest.raises(HTTPException) as exc_info:
        login_user(bad_login, db=db_session)
    assert exc_info.value.status_code == 401


def test_api_register_without_consent_rejected(db_session):
    reg_req = UserRegisterRequest(
        username="noconsent_user",
        password="password123",
        display_name="No Consent",
        consent_given=False
    )
    with pytest.raises(HTTPException) as exc_info:
        register_account(reg_req, db=db_session)
    assert exc_info.value.status_code == 400
    assert "Consent to process dietary and health preferences is required" in exc_info.value.detail


def test_api_admin_login():
    # Valid admin key
    res = login_admin(AdminLoginRequest(admin_key="foodlens_admin_secret"))
    assert res.success is True
    assert res.admin_authenticated is True

    # Invalid admin key
    with pytest.raises(HTTPException) as exc_info:
        login_admin(AdminLoginRequest(admin_key="wrong_key"))
    assert exc_info.value.status_code == 401


def test_api_list_profiles(db_session):
    reg_req = UserRegisterRequest(
        username="user_one",
        password="password123",
        display_name="User One",
        consent_given=True
    )
    register_account(reg_req, db=db_session)

    profiles = list_available_profiles(db=db_session)
    assert len(profiles) >= 1
    assert any(p.username == "user_one" for p in profiles)
