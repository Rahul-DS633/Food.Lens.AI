"""
Unit tests for FoodLens Authentication & Security Engine
Validates password hashing, constant-time verification, DPDP consent enforcement,
and administrative access control.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base, User, UserProfile, UserProgress
from foodlens.auth import (
    hash_password,
    verify_password,
    verify_admin_key,
    authenticate_user,
    register_user,
    validate_username,
)


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_hash_and_verify_password():
    raw_pwd = "SuperSecretPassword123"
    hashed = hash_password(raw_pwd)

    assert hashed.startswith("pbkdf2:sha256:100000$")
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(raw_pwd, "") is False


def test_empty_password_raises():
    with pytest.raises(ValueError):
        hash_password("")


def test_verify_admin_key():
    assert verify_admin_key("foodlens_admin_secret") is True
    assert verify_admin_key("wrong_key") is False
    assert verify_admin_key("") is False


def test_validate_username():
    valid, _ = validate_username("rahul_rajak")
    assert valid is True

    valid, err = validate_username("ab")
    assert valid is False
    assert "at least 3 characters" in err

    valid, err = validate_username("user with spaces")
    assert valid is False


def test_register_user_dpdp_consent(test_db):
    # Missing consent must fail under DPDP Act 2023
    with pytest.raises(ValueError, match="Consent to process dietary and health preferences is required"):
        register_user(
            db=test_db,
            username="testuser1",
            password="password123",
            display_name="Test User",
            consent_given=False
        )

    # Minor without parental consent must fail
    with pytest.raises(ValueError, match="Verifiable parental/guardian consent is required"):
        register_user(
            db=test_db,
            username="testminor",
            password="password123",
            display_name="Test Minor",
            age=15,
            consent_given=True,
            parental_consent_given=False
        )

    # Valid registration
    user = register_user(
        db=test_db,
        username="health_fan",
        password="safe_password",
        display_name="Health Fan",
        email="health@example.com",
        age=28,
        allergies=["peanut", "milk"],
        custom_allergens="artificial color",
        consent_given=True
    )

    assert user.id is not None
    assert user.username == "health_fan"
    assert user.role == "user"
    assert verify_password("safe_password", user.password_hash) is True

    # Check profile
    prof = test_db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    assert prof is not None
    assert prof.allergies_json == ["peanut", "milk"]
    assert prof.consent_given is True

    # Check starting progress
    prog = test_db.query(UserProgress).filter(UserProgress.user_id == user.id).first()
    assert prog is not None
    assert prog.xp == 25
    assert prog.level == "Label Rookie"


def test_duplicate_username_fails(test_db):
    register_user(
        db=test_db,
        username="unique_user",
        password="password123",
        display_name="User One",
        consent_given=True
    )

    with pytest.raises(ValueError, match="already registered"):
        register_user(
            db=test_db,
            username="unique_user",
            password="anotherpassword",
            display_name="User Two",
            consent_given=True
        )


def test_authenticate_user(test_db):
    user = register_user(
        db=test_db,
        username="auth_tester",
        password="mypassword",
        display_name="Auth Tester",
        email="auth@foodlens.ai",
        consent_given=True
    )

    # Auth by username
    authenticated = authenticate_user(test_db, "auth_tester", "mypassword")
    assert authenticated is not None
    assert authenticated.id == user.id

    # Auth by email
    authenticated_by_email = authenticate_user(test_db, "auth@foodlens.ai", "mypassword")
    assert authenticated_by_email is not None
    assert authenticated_by_email.id == user.id

    # Wrong password
    assert authenticate_user(test_db, "auth_tester", "wrongpass") is None

    # Unknown user
    assert authenticate_user(test_db, "nonexistent", "mypassword") is None

