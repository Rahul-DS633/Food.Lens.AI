"""
FoodLens Data Reports API Route (Public User Reporting)
Enables users and guests to report inaccurate product or nutrition information.
"""

import hashlib
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List

from api.deps import get_db
from api.schemas import DataReportSubmitRequest, DataReportResponse
from db.models import Product, DataReport, Nutrition
from foodlens.report_checks import (
    validate_proposed_field,
    detect_duplicate_report,
    calculate_priority_score,
)

router = APIRouter(prefix="/api/reports", tags=["Data Reports"])


@router.post("/submit")
def submit_data_report(
    req: DataReportSubmitRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Submits a correction or issue for a product field.
    Auto-checks for plausibility and duplicates.
    """
    if not req.consent_no_personal_data:
        raise HTTPException(
            status_code=400,
            detail="You must confirm you are not sharing personal information in the report comment."
        )

    prod = db.query(Product).filter(Product.id == req.product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found.")

    # Determine reporter hash from header, IP, or user-agent
    client_ip = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("user-agent", "")
    reporter_hash = req.reporter_hash or hashlib.sha256(f"{client_ip}:{ua}".encode("utf-8")).hexdigest()[:16]

    # Contextual nutrients for validation
    current_nutrients: Dict[str, Any] = {}
    if prod.nutrition:
        n = prod.nutrition
        current_nutrients = {
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

    # Current value if not provided
    cur_val = req.current_value
    if cur_val is None:
        if hasattr(prod, req.field):
            cur_val = str(getattr(prod, req.field) or "")
        elif prod.nutrition and hasattr(prod.nutrition, req.field):
            cur_val = str(getattr(prod.nutrition, req.field) or "")

    # Execute deterministic auto-checks
    check_result = validate_proposed_field(req.field, req.proposed_value, current_nutrients)

    # Check for duplicates on the same product
    existing_reports_db = db.query(DataReport).filter(
        DataReport.product_id == req.product_id,
        DataReport.status.in_(["pending", "needs_info"])
    ).all()
    existing_reports = [
        {"id": r.id, "field": r.field, "proposed_value": r.proposed_value, "status": r.status}
        for r in existing_reports_db
    ]

    dup = detect_duplicate_report(req.field, req.proposed_value, existing_reports)
    status_str = "pending"
    dup_id = None
    consensus_count = 1

    if dup:
        dup_id = dup["id"]
        consensus_count = len([
            r for r in existing_reports
            if r["field"] == req.field and str(r["proposed_value"]).strip().lower() == req.proposed_value.strip().lower()
        ]) + 1

    priority_score = calculate_priority_score(
        consensus_count=consensus_count,
        ocr_match_score=0.0,
        has_validation_flags=not check_result.is_plausible
    )

    auto_checks_json = {
        "is_plausible": check_result.is_plausible,
        "flags": check_result.flags,
        "duplicate_of_id": dup_id,
        "consensus_count": consensus_count,
    }

    report = DataReport(
        product_id=req.product_id,
        field=req.field,
        current_value=cur_val,
        proposed_value=req.proposed_value,
        comment=req.comment or "",
        reporter_hash=reporter_hash,
        status=status_str,
        priority_score=priority_score,
        auto_checks_json=auto_checks_json,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return {
        "report_id": report.id,
        "status": report.status,
        "priority_score": report.priority_score,
        "message": "Report received and queued for admin review. Thank you for helping keep FoodLens data accurate.",
    }


@router.get("/{report_id}", response_model=DataReportResponse)
def get_report_status(report_id: int, db: Session = Depends(get_db)):
    """
    Checks the status of a submitted data report.
    """
    report = db.query(DataReport).filter(DataReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    return DataReportResponse(
        id=report.id,
        product_id=report.product_id,
        field=report.field,
        current_value=report.current_value,
        proposed_value=report.proposed_value,
        evidence_image_path=report.evidence_image_path,
        comment=report.comment,
        status=report.status,
        priority_score=report.priority_score,
        auto_checks=report.auto_checks_json,
        created_at=report.created_at.isoformat() if report.created_at else None,
        reviewed_by=report.reviewed_by,
        reviewed_at=report.reviewed_at.isoformat() if report.reviewed_at else None,
        reviewer_note=report.reviewer_note,
    )
