"""
FoodLens Nutrition Calculation Route
Deterministic live recalculation for custom grams, servings, or whole packet.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.deps import get_db
from api.schemas import CalculatePortionRequest
from db.models import Product
from foodlens.nutrition import (
    NutritionProfile, create_nutrient, calculate_portion
)

router = APIRouter(prefix="/api/nutrition", tags=["Nutrition"])


@router.post("/calculate")
def calculate_nutritional_portion(
    req: CalculatePortionRequest,
    db: Session = Depends(get_db)
):
    """
    Portion calculation: 100g, serving, packet, or custom grams.
    Returns scaled nutrients and equivalent sugar teaspoons.
    """
    profile = None

    if req.product_id:
        prod = db.query(Product).filter(Product.id == req.product_id).first()
        if not prod or not prod.nutrition:
            raise HTTPException(status_code=404, detail="Product or nutrition data not found.")

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
            serving_size_g=prod.serving_size_g,
            net_weight_g=prod.net_weight_g,
            is_beverage=(prod.category in ("beverages", "drinks"))
        )
    elif req.nutrition_data:
        nd = req.nutrition_data
        nutr = nd.get("nutrients", {})
        profile = NutritionProfile(
            basis="per_100g",
            energy_kcal=create_nutrient(nutr.get("energy_kcal", {}).get("value") if isinstance(nutr.get("energy_kcal"), dict) else nutr.get("energy_kcal"), "kcal"),
            protein_g=create_nutrient(nutr.get("protein_g", {}).get("value") if isinstance(nutr.get("protein_g"), dict) else nutr.get("protein_g"), "g"),
            carbs_g=create_nutrient(nutr.get("carbs_g", {}).get("value") if isinstance(nutr.get("carbs_g"), dict) else nutr.get("carbs_g"), "g"),
            sugars_g=create_nutrient(nutr.get("sugars_g", {}).get("value") if isinstance(nutr.get("sugars_g"), dict) else nutr.get("sugars_g"), "g"),
            added_sugar_g=create_nutrient(nutr.get("added_sugar_g", {}).get("value") if isinstance(nutr.get("added_sugar_g"), dict) else nutr.get("added_sugar_g"), "g"),
            fat_g=create_nutrient(nutr.get("fat_g", {}).get("value") if isinstance(nutr.get("fat_g"), dict) else nutr.get("fat_g"), "g"),
            sat_fat_g=create_nutrient(nutr.get("sat_fat_g", {}).get("value") if isinstance(nutr.get("sat_fat_g"), dict) else nutr.get("sat_fat_g"), "g"),
            trans_fat_g=create_nutrient(nutr.get("trans_fat_g", {}).get("value") if isinstance(nutr.get("trans_fat_g"), dict) else nutr.get("trans_fat_g"), "g"),
            fibre_g=create_nutrient(nutr.get("fibre_g", {}).get("value") if isinstance(nutr.get("fibre_g"), dict) else nutr.get("fibre_g"), "g"),
            sodium_mg=create_nutrient(nutr.get("sodium_mg", {}).get("value") if isinstance(nutr.get("sodium_mg"), dict) else nutr.get("sodium_mg"), "mg"),
            serving_size_g=nd.get("serving_size_g"),
            net_weight_g=nd.get("net_weight_g"),
            is_beverage=nd.get("is_beverage", False)
        )
    else:
        raise HTTPException(status_code=400, detail="Must provide product_id or nutrition_data.")

    try:
        scaled = calculate_portion(
            profile,
            portion_type=req.portion_type,
            custom_grams=req.custom_grams,
            servings=req.servings
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "status": "success",
        "portion_type": req.portion_type,
        "scaled_profile": scaled.to_dict(),
        "sugar_teaspoons": scaled.sugar_teaspoons,
        "salt_g": scaled.salt_g,
    }

