"""
FoodLens Hidden Sugar Detection API Route
Analyzes ingredient lists for hidden sugars, syrups, concentrates, sweeteners,
sugar splitting, and label conflicts.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from api.deps import get_db
from api.schemas import SugarAnalyzeRequest, SugarReportResponse, SugarMatchSchema
from db.models import Product
from foodlens.sugar_detector import SugarDetector
from foodlens.advisor import AIAdvisor

router = APIRouter(prefix="/api/sugar", tags=["Sugar Intelligence"])

detector = SugarDetector()
advisor = AIAdvisor()


@router.post("/analyze", response_model=SugarReportResponse)
def analyze_hidden_sugars(
    req: SugarAnalyzeRequest,
    db: Session = Depends(get_db)
):
    """
    Detects all sugar-type ingredients, syrups, sweeteners, and bulking agents.
    Cross-checks nutrition label for zero-added-sugar conflicts and computes teaspoons.
    """
    ingredients_text = req.ingredients_text or ""
    product_name = "Packaged Product"
    added_sugar_g = req.added_sugar_g
    total_sugars_g = req.total_sugars_g
    portion_g = req.portion_g

    if req.product_id:
        prod = db.query(Product).filter(Product.id == req.product_id).first()
        if not prod:
            raise HTTPException(status_code=404, detail="Product not found.")
        product_name = prod.name
        if not ingredients_text and prod.ingredients:
            ingredients_text = ", ".join([f"{ing.name}" for ing in prod.ingredients])

        if prod.nutrition:
            n = prod.nutrition
            scale_factor = portion_g / 100.0
            if added_sugar_g is None and n.added_sugar_g is not None:
                added_sugar_g = round(n.added_sugar_g * scale_factor, 2)
            if total_sugars_g is None and n.sugars_g is not None:
                total_sugars_g = round(n.sugars_g * scale_factor, 2)

    report = detector.detect_sugars(
        ingredients_text=ingredients_text,
        added_sugar_g=added_sugar_g,
        total_sugars_g=total_sugars_g,
        portion_g=portion_g,
    )

    advisor_payload = {
        "product_name": product_name,
        "sugar_report": report.to_dict(),
    }
    ai_explanation = advisor.generate_sugar_explanation(advisor_payload)

    return SugarReportResponse(
        matches=[
            SugarMatchSchema(
                ingredient_text=m.ingredient_text,
                normalized_alias=m.normalized_alias,
                sugar_class=m.sugar_class,
                position=m.position,
                confidence=m.confidence,
                match_type=m.match_type,
                is_added=m.is_added,
                explanation=m.explanation,
            )
            for m in report.matches
        ],
        distinct_sugar_names=report.distinct_sugar_names,
        first_sugar_position=report.first_sugar_position,
        sugars_in_top3=report.sugars_in_top3,
        sugar_splitting=report.sugar_splitting,
        non_sugar_sweeteners=report.non_sugar_sweeteners,
        carb_fillers=report.carb_fillers,
        label_conflict=report.label_conflict,
        label_conflict_reason=report.label_conflict_reason,
        portion_teaspoons=report.portion_teaspoons,
        teaspoon_basis=report.teaspoon_basis,
        ai_summary=ai_explanation.get("summary", ""),
        status=report.status,
    )

