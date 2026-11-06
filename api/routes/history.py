"""
FoodLens Scan History Route
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from api.deps import get_db
from db.models import Scan, Product

router = APIRouter(prefix="/api/history", tags=["History"])


@router.get("")
def get_user_history(
    user_id: int = 1,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    scans = (
        db.query(Scan)
        .filter(Scan.user_id == user_id)
        .order_by(Scan.created_at.desc())
        .limit(limit)
        .all()
    )

    results = []
    for s in scans:
        prod = s.product
        results.append({
            "scan_id": s.id,
            "product_id": s.product_id,
            "product_name": prod.name if prod else "Unknown",
            "brand": prod.brand if prod else "",
            "category": prod.category if prod else "",
            "image_url": prod.image_url if prod else "",
            "score": s.score,
            "source_type": s.source_type,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })

    return {
        "user_id": user_id,
        "count": len(results),
        "history": results,
    }

