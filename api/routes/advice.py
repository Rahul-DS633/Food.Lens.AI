"""
FoodLens AI Advice Route
Generates grounded nutrition explanations with strict number verification post-check.
"""

from fastapi import APIRouter, HTTPException
from api.schemas import AdviceRequest
from foodlens.advisor import AIAdvisor

router = APIRouter(prefix="/api/advice", tags=["Advice"])

advisor = AIAdvisor()


@router.post("")
def get_nutrition_advice(req: AdviceRequest):
    """
    Accepts validated product payload.
    Returns structured explanation verified against all input numbers.
    """
    if not req.payload:
        raise HTTPException(status_code=400, detail="Missing payload data.")

    explanation = advisor.generate_explanation(req.payload)

    return {
        "status": "success",
        "explanation": explanation.to_dict(),
        "is_grounded": explanation.is_grounded,
        "evidence_numbers_used": explanation.evidence_numbers_used,
        "flagged_numbers": explanation.flagged_numbers,
    }

