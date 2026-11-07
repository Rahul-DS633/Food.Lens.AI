"""
FoodLens Claims API Route
Endpoints for detecting and evaluating front-of-pack claims against verified product data.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas import (
    ClaimCheckRequest,
    ClaimCheckResponse,
    ClaimEvidenceSchema,
    ClaimResultSchema,
)
from db.models import Product
from foodlens.advisor import AIAdvisor
from foodlens.claims import ClaimChecker
from foodlens.nutrition import NutritionProfile, create_nutrient

router = APIRouter(prefix="/api/claims", tags=["Claim Checker"])


@router.post("/check", response_model=ClaimCheckResponse)
def check_product_claims(
    req: ClaimCheckRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluates marketing claims against verified product nutrition and ingredients.
    """
    prod: Optional[Product] = None
    ingredients_text = req.ingredients_text or ""

    if req.product_id is not None:
        prod = db.query(Product).filter(Product.id == req.product_id).first()
        if not prod:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {req.product_id} not found"
            )

        if not ingredients_text and prod.ingredients:
            sorted_ings = sorted(prod.ingredients, key=lambda x: x.position)
            ingredients_text = ", ".join(i.name for i in sorted_ings if i.name)

    # Reconstruct NutritionProfile
    if prod and prod.nutrition:
        n = prod.nutrition
        basis = n.basis or "per_100g"
        profile = NutritionProfile(
            basis=basis,
            energy_kcal=create_nutrient(n.energy_kcal, "kcal", basis),
            protein_g=create_nutrient(n.protein_g, "g", basis),
            carbs_g=create_nutrient(n.carbs_g, "g", basis),
            sugars_g=create_nutrient(n.sugars_g, "g", basis),
            added_sugar_g=create_nutrient(n.added_sugar_g, "g", basis),
            fat_g=create_nutrient(n.fat_g, "g", basis),
            sat_fat_g=create_nutrient(n.sat_fat_g, "g", basis),
            trans_fat_g=create_nutrient(n.trans_fat_g, "g", basis),
            fibre_g=create_nutrient(n.fibre_g, "g", basis),
            sodium_mg=create_nutrient(n.sodium_mg, "mg", basis),
            serving_size_g=prod.serving_size_g,
            is_beverage=(prod.category == "beverage" or "ml" in basis),
        )
    else:
        profile = NutritionProfile(basis="per_100g")

    checker = ClaimChecker()
    summary = checker.check_claims(req.claims, profile, ingredients_text=ingredients_text)

    advisor = AIAdvisor()
    prod_name = prod.name if prod else "Packaged Product"
    ai_summary = advisor.explain_claim_check(summary, product_name=prod_name)

    results_out = [
        ClaimResultSchema(
            claim_text=r.claim_text,
            rule_id=r.rule_id,
            status=r.status.value,
            evidence=[
                ClaimEvidenceSchema(field=e.field, value=e.value, basis=e.basis)
                for e in r.evidence
            ],
            threshold_value=r.threshold_value,
            threshold_operator=r.threshold_operator,
            threshold_source=r.threshold_source,
            confidence=r.confidence,
            missing_fields=list(r.missing_fields),
            neutral_explanation=r.neutral_explanation,
            disclaimer=r.disclaimer,
        )
        for r in summary.results
    ]

    return ClaimCheckResponse(
        total_claims=summary.total_claims,
        supported_count=summary.supported_count,
        partly_supported_count=summary.partly_supported_count,
        not_supported_count=summary.not_supported_count,
        cannot_verify_count=summary.cannot_verify_count,
        not_checkable_count=summary.not_checkable_count,
        summary_sentence=summary.summary_sentence,
        results=results_out,
        ai_summary=ai_summary,
    )
