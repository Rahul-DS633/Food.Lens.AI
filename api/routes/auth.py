"""
FoodLens Authentication & Session API Routes
Provides endpoints for user sign-in, account registration with DPDP Act consent,
admin key authentication, and profile switching.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas import (
    UserLoginRequest,
    AdminLoginRequest,
    UserRegisterRequest,
    AuthUserResponse,
    AuthLoginResponse,
)
from db.models import User
from foodlens.auth import (
    authenticate_user,
    register_user,
    verify_admin_key,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication & Access"])


def _user_to_response(user: User) -> AuthUserResponse:
    progress = user.progress
    xp = progress.xp if progress else 25
    level = progress.level if progress else "Label Rookie"
    streak = progress.current_streak if progress else 1

    role = getattr(user, "role", "user") or "user"
    return AuthUserResponse(
        id=user.id,
        username=user.username,
        display_name=user.display_name or "User",
        email=user.email,
        role=role,
        language=user.language or "en",
        level=level,
        xp=xp,
        streak=streak,
    )


@router.post("/login", response_model=AuthLoginResponse)
def login_user(req: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates a user using username or email and password.
    """
    user = authenticate_user(db, req.identifier, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password."
        )

    return AuthLoginResponse(
        success=True,
        message=f"Welcome back, {user.display_name}!",
        user=_user_to_response(user),
        admin_authenticated=(getattr(user, "role", "user") == "admin"),
    )


@router.post("/register", response_model=AuthLoginResponse, status_code=status.HTTP_201_CREATED)
def register_account(req: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Registers a new user account with mandatory DPDP Act 2023 consent validation.
    """
    try:
        new_user = register_user(
            db=db,
            username=req.username,
            password=req.password,
            display_name=req.display_name,
            email=req.email,
            age=req.age,
            weight_kg=req.weight_kg,
            allergies=req.allergies,
            custom_allergens=req.custom_allergens,
            consent_given=req.consent_given,
            parental_consent_given=req.parental_consent_given,
            language=req.language,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return AuthLoginResponse(
        success=True,
        message="Account created successfully with personalized dietary protection active.",
        user=_user_to_response(new_user),
        admin_authenticated=False,
    )


@router.post("/admin-login", response_model=AuthLoginResponse)
def login_admin(req: AdminLoginRequest):
    """
    Authenticates administrator access using the system admin key.
    """
    is_admin = verify_admin_key(req.admin_key)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrator key or password."
        )

    return AuthLoginResponse(
        success=True,
        message="Administrator session verified successfully.",
        user=None,
        admin_authenticated=True,
    )


@router.get("/profiles", response_model=List[AuthUserResponse])
def list_available_profiles(db: Session = Depends(get_db)):
    """
    Returns available user profiles for quick switching on local/offline devices.
    """
    users = db.query(User).order_by(User.id.asc()).all()
    return [_user_to_response(u) for u in users]

