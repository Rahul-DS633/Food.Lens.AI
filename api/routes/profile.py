"""
FoodLens User Profile & Consent Management Routes
Supports DPDP Act compliant profile creation, retrieval, export, and deletion.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas import UserProfileCreate, UserProfileResponse
from db.models import User, UserProfile, Achievement, UserAchievement, utcnow
from db.session import export_user_data, delete_user_data

router = APIRouter(prefix="/api/profile", tags=["Profile & Privacy"])


@router.post("", response_model=UserProfileResponse)
def save_user_profile(
    req: UserProfileCreate,
    db: Session = Depends(get_db)
):
    """
    Creates or updates user profile with mandatory consent validation.
    Under India's DPDP Act, users under 18 require parental consent.
    """
    if not req.consent_given:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consent to process dietary preferences is required."
        )

    if req.age < 18 and not req.parental_consent_given:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verifiable parental/guardian consent is required for users under 18 under DPDP Act."
        )

    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        user = User(id=req.user_id, display_name=req.name, language=req.language)
        db.add(user)
        db.flush()
    else:
        user.display_name = req.name
        user.language = req.language

    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        profile = UserProfile(
            user_id=user.id,
            name=req.name,
            age=req.age,
            weight_kg=req.weight_kg,
            allergies_json=req.allergies,
            custom_allergens_text=req.custom_allergens,
            language=req.language,
            consent_given=req.consent_given,
            parental_consent_given=req.parental_consent_given,
            consent_timestamp=utcnow(),
        )
        db.add(profile)
    else:
        profile.name = req.name
        profile.age = req.age
        profile.weight_kg = req.weight_kg
        profile.allergies_json = req.allergies
        profile.custom_allergens_text = req.custom_allergens
        profile.language = req.language
        profile.consent_given = req.consent_given
        profile.parental_consent_given = req.parental_consent_given
        profile.updated_at = utcnow()

    # Award "PROFILE_SET_UP" badge if name and preferences set
    ach = db.query(Achievement).filter(Achievement.code == "PROFILE_SET_UP").first()
    if ach:
        existing_ach = db.query(UserAchievement).filter(
            UserAchievement.user_id == user.id,
            UserAchievement.achievement_id == ach.id
        ).first()
        if not existing_ach:
            db.add(UserAchievement(user_id=user.id, achievement_id=ach.id))

    db.commit()
    db.refresh(profile)

    return UserProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        name=profile.name,
        age=profile.age,
        weight_kg=profile.weight_kg,
        allergies=profile.allergies_json or [],
        custom_allergens=profile.custom_allergens_text or "",
        language=profile.language,
        consent_given=profile.consent_given,
        parental_consent_given=profile.parental_consent_given,
        consent_timestamp=profile.consent_timestamp.isoformat() if profile.consent_timestamp else None,
    )


@router.get("/{user_id}", response_model=UserProfileResponse)
def get_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    return UserProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        name=profile.name,
        age=profile.age,
        weight_kg=profile.weight_kg,
        allergies=profile.allergies_json or [],
        custom_allergens=profile.custom_allergens_text or "",
        language=profile.language,
        consent_given=profile.consent_given,
        parental_consent_given=profile.parental_consent_given,
        consent_timestamp=profile.consent_timestamp.isoformat() if profile.consent_timestamp else None,
    )


@router.delete("/{user_id}")
def delete_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Deletes all personal data under DPDP Act right to erasure.
    """
    success = delete_user_data(user_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"status": "success", "message": "All personal data erased successfully."}


@router.get("/{user_id}/export")
def export_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Exports user profile and scan history under DPDP Act right to data portability.
    """
    data = export_user_data(user_id, db)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data

