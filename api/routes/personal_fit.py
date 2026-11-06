"""
FoodLens Personalized Food Fit Route
Deterministic dietary cross-checking and grounded AI advice.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List

from api.deps import get_db
from api.schemas import PersonalFitRequest, PersonalFitResponse
from db.models import Product, UserProfile
from foodlens.nutrition import NutritionProfile, create_nutrient
from foodlens.personal_fit import PersonalFitEngine, UserProfileData
from foodlens.advisor import AIAdvisor

router = APIRouter(prefix="/api/personal-fit", tags=["Personal Fit"])

fit_engine = PersonalFitEngine()
advisor = AIAdvisor()


@router.post("", response_model=PersonalFitResponse)
def calculate_personal_fit(
    req: PersonalFitRequest,
    db: Session = Depends(get_db)
):
    """
    Computes personalized food fit, allergen cross-check, and grounded advice.
    Supports both registered users (by user_id) and guest users (via profile_override).
    """
    # 1. Resolve Product & Nutritional Profile
    product_name = "Packaged Food"
    category = "general"
    ingredients_text = req.ingredients_text or ""
    serving_size_g = 25.0
    net_weight_g = 100.0
    profile = None

    if req.product_id:
        prod = db.query(Product).filter(Product.id == req.product_id).first()
        if not prod or not prod.nutrition:
            raise HTTPException(status_code=404, detail="Product or nutrition data not found.")
        product_name = prod.name
        category = prod.category or "general"
        serving_size_g = prod.serving_size_g or 25.0
        net_weight_g = prod.net_weight_g or 100.0

        if not ingredients_text and prod.ingredients:
            ingredients_text = ", ".join([f"{ing.name}" for ing in prod.ingredients])

        n = prod.nutrition
        profile = NutritionProfile(
            basis="per_100g",
            energy_kcal=create_nutrient(n.energy_kcal, "kcal", basis="per_100g"),
            protein_g=create_nutrient(n.protein_g, "g", basis="per_100g"),
            carbs_g=create_nutrient(n.carbs_g, "g", basis="per_100g"),
            sugars_g=create_nutrient(n.sugars_g, "g", basis="per_100g"),
            added_sugar_g=create_nutrient(n.added_sugar_g, "g", basis="per_100g"),
            fat_g=create_nutrient(n.fat_g, "g", basis="per_100g"),
            sat_fat_g=create_nutrient(n.sat_fat_g, "g", basis="per_100g"),
            trans_fat_g=create_nutrient(n.trans_fat_g, "g", basis="per_100g"),
            fibre_g=create_nutrient(n.fibre_g, "g", basis="per_100g"),
            sodium_mg=create_nutrient(n.sodium_mg, "mg", basis="per_100g"),
            serving_size_g=serving_size_g,
            net_weight_g=net_weight_g,
        )
    elif req.nutrition_data:
        nd = req.nutrition_data
        serving_size_g = float(nd.get("serving_size_g") or 25.0)
        net_weight_g = float(nd.get("net_weight_g") or 100.0)
        product_name = nd.get("product_name", "Packaged Food")
        category = nd.get("category", "general")
        profile = NutritionProfile(
            basis="per_100g",
            energy_kcal=create_nutrient(nd.get("energy_kcal"), "kcal"),
            protein_g=create_nutrient(nd.get("protein_g"), "g"),
            carbs_g=create_nutrient(nd.get("carbs_g"), "g"),
            sugars_g=create_nutrient(nd.get("sugars_g"), "g"),
            added_sugar_g=create_nutrient(nd.get("added_sugar_g"), "g"),
            fat_g=create_nutrient(nd.get("fat_g"), "g"),
            sat_fat_g=create_nutrient(nd.get("sat_fat_g"), "g"),
            trans_fat_g=create_nutrient(nd.get("trans_fat_g"), "g"),
            fibre_g=create_nutrient(nd.get("fibre_g"), "g"),
            sodium_mg=create_nutrient(nd.get("sodium_mg"), "mg"),
            serving_size_g=serving_size_g,
            net_weight_g=net_weight_g,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either product_id or nutrition_data must be provided."
        )

    # 2. Resolve Portion Grams
    if req.portion_type == "100g":
        portion_grams = 100.0
    elif req.portion_type == "serving":
        portion_grams = serving_size_g
    elif req.portion_type == "packet":
        portion_grams = net_weight_g
    elif req.portion_type == "custom":
        portion_grams = float(req.custom_grams or 100.0)
    else:
        portion_grams = 100.0

    # 3. Resolve User Profile
    if req.profile_override:
        po = req.profile_override
        custom_algs = [c.strip() for c in po.custom_allergens.split(",") if c.strip()]
        user_data = UserProfileData(
            name=po.name,
            age=po.age,
            weight_kg=po.weight_kg,
            allergies=po.allergies,
            custom_allergens=custom_algs,
            language=po.language,
            consent_given=po.consent_given,
            parental_consent_given=po.parental_consent_given,
        )
    elif req.user_id:
        db_prof = db.query(UserProfile).filter(UserProfile.user_id == req.user_id).first()
        if db_prof:
            custom_algs = [c.strip() for c in (db_prof.custom_allergens_text or "").split(",") if c.strip()]
            user_data = UserProfileData(
                name=db_prof.name,
                age=db_prof.age,
                weight_kg=db_prof.weight_kg,
                allergies=db_prof.allergies_json or [],
                custom_allergens=custom_algs,
                language=db_prof.language,
                consent_given=db_prof.consent_given,
                parental_consent_given=db_prof.parental_consent_given,
            )
        else:
            user_data = UserProfileData(name="Guest", age=25, allergies=[])
    else:
        user_data = UserProfileData(name="Guest", age=25, allergies=[])

    # 4. Pure Python Deterministic Fit Calculation
    fit = fit_engine.calculate_fit(
        profile=profile,
        user=user_data,
        portion_grams=portion_grams,
        ingredients_text=ingredients_text,
    )

    # 5. Grounded AI Explanation (User name is strictly omitted)
    advisor_payload = advisor.build_personal_fit_payload(
        fit=fit,
        product_name=product_name,
        category=category,
        user_name=user_data.name,
        user_age=user_data.age,
        user_weight_kg=user_data.weight_kg,
    )
    explanation = advisor.generate_personal_fit_explanation(advisor_payload)

    return PersonalFitResponse(
        verdict=fit.verdict.value,
        portion_grams=fit.portion_grams,
        confidence=fit.confidence,
        allergen_check=fit.allergen_check.to_dict(),
        nutrient_flags=[
            {
                "nutrient": f.nutrient,
                "display_name": f.display_name,
                "portion_value": f.portion_value,
                "reference_value": f.reference_value,
                "pct_of_reference": f.pct_of_reference,
                "unit": f.unit,
                "severity": f.severity,
                "reason": f.reason,
            }
            for f in fit.nutrient_flags
        ],
        missing_data=fit.missing_data,
        guidance_notes=fit.guidance_notes,
        ai_explanation=explanation.to_dict(),
        disclaimer=fit.disclaimer,
    )

