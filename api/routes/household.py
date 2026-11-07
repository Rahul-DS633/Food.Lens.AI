"""
FoodLens Household & Family Profiles API Route
CRUD management of family members and multi-person product fit checks.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas import (
    FamilyCheckRequest,
    FamilyCheckResponse,
    HouseholdMemberCreate,
    HouseholdMemberResponse,
    HouseholdResponse,
)
from db.models import Household, HouseholdMember, Product
from foodlens.family_fit import (
    FamilyMemberInput,
    HouseholdFitEngine,
)
from foodlens.nutrition import NutritionProfile, create_nutrient

router = APIRouter(prefix="/api/household", tags=["Family Profiles"])
family_engine = HouseholdFitEngine()


@router.get("", response_model=HouseholdResponse)
def create_or_get_household(user_id: int = 1, db: Session = Depends(get_db)):
    """
    Retrieves or creates the user's primary household.
    """
    hh = db.query(Household).filter(Household.owner_user_id == user_id).first()
    if not hh:
        hh = Household(owner_user_id=user_id)
        db.add(hh)
        db.commit()
        db.refresh(hh)

    members_res = [
        HouseholdMemberResponse(
            id=m.id,
            household_id=m.household_id,
            display_name=m.display_name,
            emoji_avatar=m.emoji_avatar,
            age=m.age,
            weight_kg=m.weight_kg,
            allergies=m.allergies_json or [],
            dietary_prefs=m.dietary_prefs_json or [],
            is_minor=m.is_minor,
            consent_by_owner=m.consent_by_owner,
            created_at=m.created_at.isoformat() if m.created_at else None,
        )
        for m in hh.members
    ]

    return HouseholdResponse(
        id=hh.id,
        owner_user_id=hh.owner_user_id,
        members=members_res,
        created_at=hh.created_at.isoformat() if hh.created_at else None,
    )


@router.post("/members", response_model=HouseholdMemberResponse)
def add_household_member(
    req: HouseholdMemberCreate,
    user_id: int = 1,
    db: Session = Depends(get_db),
):
    """
    Adds a new member to the user's household. Enforces maximum 8 members limit.
    """
    hh = db.query(Household).filter(Household.owner_user_id == user_id).first()
    if not hh:
        hh = Household(owner_user_id=user_id)
        db.add(hh)
        db.commit()
        db.refresh(hh)

    current_count = db.query(HouseholdMember).filter(HouseholdMember.household_id == hh.id).count()
    if current_count >= 8:
        raise HTTPException(
            status_code=400,
            detail="A household cannot exceed 8 members."
        )

    is_minor = req.age < 18
    member = HouseholdMember(
        household_id=hh.id,
        display_name=req.display_name.strip(),
        emoji_avatar=req.emoji_avatar or "👤",
        age=req.age,
        weight_kg=req.weight_kg if not is_minor else None,
        allergies_json=req.allergies or [],
        dietary_prefs_json=req.dietary_prefs or [],
        is_minor=is_minor,
        consent_by_owner=req.consent_by_owner,
        consent_at=datetime.now(timezone.utc),
    )
    db.add(member)
    db.commit()
    db.refresh(member)

    return HouseholdMemberResponse(
        id=member.id,
        household_id=member.household_id,
        display_name=member.display_name,
        emoji_avatar=member.emoji_avatar,
        age=member.age,
        weight_kg=member.weight_kg,
        allergies=member.allergies_json or [],
        dietary_prefs=member.dietary_prefs_json or [],
        is_minor=member.is_minor,
        consent_by_owner=member.consent_by_owner,
        created_at=member.created_at.isoformat() if member.created_at else None,
    )


@router.put("/members/{member_id}", response_model=HouseholdMemberResponse)
def update_household_member(
    member_id: int,
    req: HouseholdMemberCreate,
    user_id: int = 1,
    db: Session = Depends(get_db),
):
    """
    Updates an existing household member profile.
    """
    member = db.query(HouseholdMember).filter(HouseholdMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found.")

    is_minor = req.age < 18
    member.display_name = req.display_name.strip()
    member.emoji_avatar = req.emoji_avatar
    member.age = req.age
    member.weight_kg = req.weight_kg if not is_minor else None
    member.allergies_json = req.allergies or []
    member.dietary_prefs_json = req.dietary_prefs or []
    member.is_minor = is_minor
    member.consent_by_owner = req.consent_by_owner

    db.commit()
    db.refresh(member)

    return HouseholdMemberResponse(
        id=member.id,
        household_id=member.household_id,
        display_name=member.display_name,
        emoji_avatar=member.emoji_avatar,
        age=member.age,
        weight_kg=member.weight_kg,
        allergies=member.allergies_json or [],
        dietary_prefs=member.dietary_prefs_json or [],
        is_minor=member.is_minor,
        consent_by_owner=member.consent_by_owner,
        created_at=member.created_at.isoformat() if member.created_at else None,
    )


@router.delete("/members/{member_id}")
def delete_household_member(
    member_id: int,
    user_id: int = 1,
    db: Session = Depends(get_db),
):
    """
    Deletes a member from the user's household.
    """
    member = db.query(HouseholdMember).filter(HouseholdMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found.")

    db.delete(member)
    db.commit()
    return {"status": "deleted", "message": "Member removed from household."}


@router.post("/check", response_model=FamilyCheckResponse)
def check_family_food_fit(
    req: FamilyCheckRequest,
    db: Session = Depends(get_db),
):
    """
    Checks product fit for multiple family members simultaneously.
    """
    prod = db.query(Product).filter(Product.id == req.product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found.")

    members = db.query(HouseholdMember).filter(HouseholdMember.id.in_(req.member_ids)).all()
    if not members:
        raise HTTPException(status_code=400, detail="No valid members found for specified IDs.")

    member_inputs = [
        FamilyMemberInput(
            id=m.id,
            display_name=m.display_name,
            age=m.age,
            weight_kg=m.weight_kg,
            allergies=m.allergies_json or [],
            emoji_avatar=m.emoji_avatar or "👤",
            dietary_prefs=m.dietary_prefs_json or [],
            is_minor=m.is_minor,
            consent_by_owner=m.consent_by_owner,
        )
        for m in members
    ]

    # Reconstruct NutritionProfile
    n = prod.nutrition
    nutrition = NutritionProfile(
        basis=n.basis if n else "per_100g",
        energy_kcal=create_nutrient(n.energy_kcal, "kcal", n.basis) if n and n.energy_kcal is not None else None,
        protein_g=create_nutrient(n.protein_g, "g", n.basis) if n and n.protein_g is not None else None,
        carbs_g=create_nutrient(n.carbs_g, "g", n.basis) if n and n.carbs_g is not None else None,
        sugars_g=create_nutrient(n.sugars_g, "g", n.basis) if n and n.sugars_g is not None else None,
        added_sugar_g=create_nutrient(n.added_sugar_g, "g", n.basis) if n and n.added_sugar_g is not None else None,
        fat_g=create_nutrient(n.fat_g, "g", n.basis) if n and n.fat_g is not None else None,
        sat_fat_g=create_nutrient(n.sat_fat_g, "g", n.basis) if n and n.sat_fat_g is not None else None,
        trans_fat_g=create_nutrient(n.trans_fat_g, "g", n.basis) if n and n.trans_fat_g is not None else None,
        fibre_g=create_nutrient(n.fibre_g, "g", n.basis) if n and n.fibre_g is not None else None,
        sodium_mg=create_nutrient(n.sodium_mg, "mg", n.basis) if n and n.sodium_mg is not None else None,
        serving_size_g=prod.serving_size_g or 25.0,
    )

    ingredients_text = ", ".join([ing.name for ing in prod.ingredients]) if prod.ingredients else ""

    fit_result = family_engine.check_household(
        members=member_inputs,
        portions_by_member=req.portions,
        nutrition=nutrition,
        ingredients_text=ingredients_text,
    )

    return FamilyCheckResponse(
        worst_allergen_status=fit_result.worst_allergen_status.value,
        top_alert_banner=fit_result.top_alert_banner,
        summary_sentence=fit_result.summary_sentence,
        members_evaluated=[m.id for m in members],
        allergen_matrix=fit_result.allergen_matrix,
        disclaimer=fit_result.disclaimer,
    )
