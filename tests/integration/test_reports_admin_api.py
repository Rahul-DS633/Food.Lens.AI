"""
Integration Tests for Data Reports and Admin Review API
Rules:
1. Public endpoint for submitting wrong data reports.
2. Protected admin endpoint with password hash verification.
3. Approval creates immutable ProductRevision and never deletes original data.
"""

import pytest
from fastapi import HTTPException
from db.session import SessionLocal, init_db
from db.models import Product, DataReport, ProductRevision
from api.routes.reports import submit_data_report, get_report_status
from api.routes.admin import list_reports_queue, approve_report, reject_report, get_admin_metrics, verify_admin_auth
from api.schemas import DataReportSubmitRequest, AdminReportReviewRequest


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


class MockRequest:
    client = type("Client", (), {"host": "127.0.0.1"})()
    headers = {"user-agent": "pytest-agent"}


def test_submit_report_as_guest_and_retrieve_status():
    db = SessionLocal()
    try:
        prod = db.query(Product).first()
        assert prod is not None

        req = DataReportSubmitRequest(
            product_id=prod.id,
            field="protein_g",
            current_value="5.0",
            proposed_value="8.0",
            comment="Front label states 8g protein per 100g.",
            consent_no_personal_data=True,
        )

        resp = submit_data_report(req, request=MockRequest(), db=db)
        assert "report_id" in resp
        assert resp["status"] == "pending"

        report_id = resp["report_id"]
        status_resp = get_report_status(report_id, db=db)
        assert status_resp.id == report_id
        assert status_resp.status == "pending"
    finally:
        db.close()


def test_admin_auth_required_for_review_routes():
    # Calling verify_admin_auth without valid key raises HTTPException 401
    with pytest.raises(HTTPException) as exc1:
        verify_admin_auth(x_admin_key=None)
    assert exc1.value.status_code == 401

    with pytest.raises(HTTPException) as exc2:
        verify_admin_auth(x_admin_key="wrong_password")
    assert exc2.value.status_code == 401

    assert verify_admin_auth(x_admin_key="foodlens_admin_secret") is True


def test_admin_approval_creates_immutable_revision():
    db = SessionLocal()
    try:
        prod = db.query(Product).first()
        orig_name = prod.name

        report = DataReport(
            product_id=prod.id,
            field="name",
            current_value=orig_name,
            proposed_value="Updated Premium Product",
            comment="Correct pack title",
            status="pending",
            priority_score=2.0,
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        req = AdminReportReviewRequest(reviewer_note="Verified from pack photo")
        resp = approve_report(report.id, req, db=db, authorized=True)
        assert resp["status"] == "approved"

        # Verify database state
        db.refresh(report)
        assert report.status == "approved"
        assert report.reviewed_by == "admin"

        # Verify ProductRevision row exists
        rev = db.query(ProductRevision).filter(ProductRevision.report_id == report.id).first()
        assert rev is not None
        assert rev.old_value == orig_name
        assert rev.new_value == "Updated Premium Product"
        assert rev.source == "user_report"

        # Verify product is updated and verification_status is admin_verified
        db.refresh(prod)
        assert prod.name == "Updated Premium Product"
        assert prod.verification_status == "admin_verified"
    finally:
        db.close()


def test_admin_metrics_summary():
    db = SessionLocal()
    try:
        metrics = get_admin_metrics(db=db, authorized=True)
        assert metrics.total_reports >= 1
        assert isinstance(metrics.approval_rate_percent, float)
        assert isinstance(metrics.most_reported_fields, list)
    finally:
        db.close()
