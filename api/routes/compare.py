"""
FoodLens Comparison Route
Side-by-side per-100g comparison for 2 to 4 products with nutrient differences highlighted.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.deps import get_db
from api.schemas import CompareRequest
from db.models import Product, UserProgress, XPEvent
from foodlens.nutrition import NutritionProfile, create_nutrient
from foodlens.scoring import calculate_foodlens_score
from foodlens.gamification.xp import calculate_xp_award

router = APIRouter(prefix="/api/compare", tags=["Compare"])


@router.post("")
def compare_products(
    req: CompareRequest,
    db: Session = Depends(get_db)
):
    """
    Compares 2-4 products per 100g.
    Computes nutrient deltas, score comparisons, and awards XP.
    """
    products = db.query(Product).filter(Product.id.in_(req.product_ids)).all()
    if len(products) < len(req.product_ids):
        raise HTTPException(status_code=404, detail="One or more product IDs not found.")

    compared_items = []
    for prod in products:
        n = prod.nutrition
        if not n:
            continue

        profile = NutritionProfile(
            basis="per_100g",
            energy_kcal=create_nutrient(n.energy_kcal, "kcal"),
            protein_g=create_nutrient(n.protein_g, "g"),
            carbs_g=create_nutrient(n.carbs_g, "g"),
            sugars_g=create_nutrient(n.sugars_g, "g"),
            added_sugar_g=create_nutrient(n.added_sugar_g, "g"),
            fat_g=create_nutrient(n.fat_g, "g"),
            sat_fat_g=create_nutrient(n.sat_fat_g, "g"),
            trans_fat_g=create_nutrient(n.trans_fat_g, "g"),
            fibre_g=create_nutrient(n.fibre_g, "g"),
            sodium_mg=create_nutrient(n.sodium_mg, "mg"),
            serving_size_g=prod.serving_size_g,
            net_weight_g=prod.net_weight_g,
        )
        score_res = calculate_foodlens_score(profile, category=prod.category)

        compared_items.append({
            "id": prod.id,
            "name": prod.name,
            "brand": prod.brand,
            "category": prod.category,
            "score": score_res.score,
            "band": score_res.band,
            "energy_kcal": n.energy_kcal,
            "protein_g": n.protein_g,
            "carbs_g": n.carbs_g,
            "sugars_g": n.sugars_g,
            "added_sugar_g": n.added_sugar_g,
            "fat_g": n.fat_g,
            "sat_fat_g": n.sat_fat_g,
            "sodium_mg": n.sodium_mg,
            "fibre_g": n.fibre_g,
            "allergens": [ing.allergen_flag for ing in prod.ingredients if ing.allergen_flag and ing.allergen_flag != "none"]
        })

    # Award comparison XP (+15 XP)
    xp_awarded = calculate_xp_award("compare")
    progress = db.query(UserProgress).filter(UserProgress.user_id == 1).first()
    if progress:
        progress.xp += xp_awarded
        db.add(XPEvent(user_id=1, event_type="compare", xp=xp_awarded, ref_id="compare_multi"))
        db.commit()

    return {
        "status": "success",
        "compared_count": len(compared_items),
        "items": compared_items,
        "xp_awarded": xp_awarded,
        "message": f"Comparison generated! +{xp_awarded} XP awarded."
    }

