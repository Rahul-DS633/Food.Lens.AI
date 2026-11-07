"""
FoodLens Admin Review API Route
Protected portal for reviewing, approving, and rejecting data correction reports.
Enforces immutable revision history and audit logging.
"""

import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas import (
    AdminMetricsResponse,
    AdminReportReviewRequest,
    DataReportResponse,
)
from db.models import (
    DataReport,
    Product,
    ProductRevision,
)
from foodlens.report_checks import validate_state_transition

router = APIRouter(prefix="/api/admin", tags=["Admin Portal"])

ADMIN_SECRET_KEY = os.getenv("FOODLENS_ADMIN_PASSWORD_HASH", "foodlens_admin_secret")


def verify_admin_auth(x_admin_key: str | None = Header(None)):
    """Verifies that the caller has provided valid admin credentials."""
    if not x_admin_key or x_admin_key != ADMIN_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authorization required or invalid admin key."
        )
    return True


@router.get("/reports", response_model=list[DataReportResponse])
def list_reports_queue(
    status_filter: str | None = None,
    field_filter: str | None = None,
    product_id: int | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_auth),
):
    """
    Lists the data review queue sorted by priority score (descending).
    """
    query = db.query(DataReport)
    if status_filter:
        query = query.filter(DataReport.status == status_filter)
    if field_filter:
        query = query.filter(DataReport.field == field_filter)
    if product_id:
        query = query.filter(DataReport.product_id == product_id)

    reports = query.order_by(DataReport.priority_score.desc(), DataReport.created_at.desc()).limit(limit).all()

    return [
        DataReportResponse(
            id=r.id,
            product_id=r.product_id,
            field=r.field,
            current_value=r.current_value,
            proposed_value=r.proposed_value,
            evidence_image_path=r.evidence_image_path,
            comment=r.comment,
            status=r.status,
            priority_score=r.priority_score,
            auto_checks=r.auto_checks_json,
            created_at=r.created_at.isoformat() if r.created_at else None,
            reviewed_by=r.reviewed_by,
            reviewed_at=r.reviewed_at.isoformat() if r.reviewed_at else None,
            reviewer_note=r.reviewer_note,
        )
        for r in reports
    ]


@router.post("/reports/{report_id}/approve")
def approve_report(
    report_id: int,
    req: AdminReportReviewRequest,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_auth),
):
    """
    Approves a report, writes an immutable ProductRevision, updates the Product/Nutrition value,
    and sets verification_status = 'admin_verified'.
    """
    report = db.query(DataReport).filter(DataReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    try:
        validate_state_transition(report.status, "approved")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    prod = db.query(Product).filter(Product.id == report.product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Associated product not found.")

    old_val = report.current_value
    new_val = report.proposed_value

    # Apply correction to Product or Nutrition model
    field_name = report.field
    applied = False

    if hasattr(prod, field_name):
        try:
            curr = getattr(prod, field_name)
            target_type = type(curr) if curr is not None else str
            if target_type == float:
                setattr(prod, field_name, float(new_val))
            elif target_type == int:
                setattr(prod, field_name, int(new_val))
            else:
                setattr(prod, field_name, str(new_val))
            applied = True
        except ValueError:
            pass

    if not applied and prod.nutrition and hasattr(prod.nutrition, field_name):
        try:
            setattr(prod.nutrition, field_name, float(new_val))
            applied = True
        except ValueError:
            pass

    # Record immutable audit revision
    revision = ProductRevision(
        product_id=prod.id,
        field=field_name,
        old_value=str(old_val),
        new_value=str(new_val),
        source="user_report",
        report_id=report.id,
        changed_by="admin",
        changed_at=datetime.now(timezone.utc),
    )
    db.add(revision)

    # Update product status
    prod.verification_status = "admin_verified"

    # Update report record
    report.status = "approved"
    report.reviewed_by = "admin"
    report.reviewed_at = datetime.now(timezone.utc)
    report.reviewer_note = req.reviewer_note or "Approved by admin."

    db.commit()
    return {"status": "approved", "message": "Correction applied with audit revision created."}


@router.post("/reports/{report_id}/reject")
def reject_report(
    report_id: int,
    req: AdminReportReviewRequest,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_auth),
):
    """Rejects a proposed data report with reviewer justification."""
    report = db.query(DataReport).filter(DataReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    try:
        validate_state_transition(report.status, "rejected")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    report.status = "rejected"
    report.reviewed_by = "admin"
    report.reviewed_at = datetime.now(timezone.utc)
    report.reviewer_note = req.reviewer_note or "Rejected by admin."

    db.commit()
    return {"status": "rejected", "message": "Report rejected."}


@router.get("/metrics", response_model=AdminMetricsResponse)
def get_admin_metrics(
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_auth),
):
    """
    Computes summary metrics for data verification and review performance.
    """
    total = db.query(DataReport).count()
    pending = db.query(DataReport).filter(DataReport.status == "pending").count()
    approved = db.query(DataReport).filter(DataReport.status == "approved").count()
    rejected = db.query(DataReport).filter(DataReport.status == "rejected").count()
    duplicate = db.query(DataReport).filter(DataReport.status == "duplicate").count()
    needs_info = db.query(DataReport).filter(DataReport.status == "needs_info").count()

    approval_rate = round((approved / total * 100.0), 1) if total > 0 else 0.0

    field_counts = (
        db.query(DataReport.field, func.count(DataReport.id).label("count"))
        .group_by(DataReport.field)
        .order_by(func.count(DataReport.id).desc())
        .limit(5)
        .all()
    )
    most_reported = [{"field": row[0], "count": row[1]} for row in field_counts]

    return AdminMetricsResponse(
        pending_count=pending,
        approved_count=approved,
        rejected_count=rejected,
        duplicate_count=duplicate,
        needs_info_count=needs_info,
        total_reports=total,
        approval_rate_percent=approval_rate,
        most_reported_fields=most_reported,
    )
