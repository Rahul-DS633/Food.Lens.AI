"""
FoodLens Products Routes
Full product record with provenance, category filtering, and search.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from api.deps import get_db
from db.models import Product

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.get("")
def list_products(
    search: Optional[str] = Query(None, description="Search by name, brand, or barcode"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            (Product.name.ilike(search_term)) |
            (Product.brand.ilike(search_term)) |
            (Product.barcode.ilike(search_term))
        )
    if category:
        query = query.filter(Product.category == category)

    products = query.order_by(Product.id.desc()).limit(50).all()
    results = []
    for p in products:
        results.append({
            "id": p.id,
            "barcode": p.barcode,
            "name": p.name,
            "brand": p.brand,
            "category": p.category,
            "net_weight_g": p.net_weight_g,
            "serving_size_g": p.serving_size_g,
            "image_url": p.image_url,
            "source": p.source,
            "verification_status": p.verification_status,
            "quality_grade": p.quality_grade,
        })
    return {"count": len(results), "products": results}


@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found.")

    nutrition_dict = {}
    if prod.nutrition:
        n = prod.nutrition
        nutrition_dict = {
            "basis": n.basis,
            "energy_kcal": n.energy_kcal,
            "protein_g": n.protein_g,
            "carbs_g": n.carbs_g,
            "sugars_g": n.sugars_g,
            "added_sugar_g": n.added_sugar_g,
            "fat_g": n.fat_g,
            "sat_fat_g": n.sat_fat_g,
            "trans_fat_g": n.trans_fat_g,
            "fibre_g": n.fibre_g,
            "sodium_mg": n.sodium_mg,
        }

    ingredients_list = []
    for ing in prod.ingredients:
        ingredients_list.append({
            "position": ing.position,
            "name": ing.name,
            "category": ing.category,
            "explanation": ing.explanation,
            "allergen_flag": ing.allergen_flag,
        })

    return {
        "id": prod.id,
        "barcode": prod.barcode,
        "name": prod.name,
        "brand": prod.brand,
        "category": prod.category,
        "net_weight_g": prod.net_weight_g,
        "serving_size_g": prod.serving_size_g,
        "image_url": prod.image_url,
        "source": prod.source,
        "retrieved_at": prod.retrieved_at.isoformat() if prod.retrieved_at else None,
        "verification_status": prod.verification_status,
        "quality_grade": prod.quality_grade,
        "nutrition": nutrition_dict,
        "ingredients": ingredients_list,
    }
