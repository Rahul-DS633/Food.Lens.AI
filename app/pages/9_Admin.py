"""
FoodLens AI — Admin Review Queue & Data Verification Portal
Protected workflow for reviewing user-submitted corrections and publishing verified product revisions.
"""

import os
import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st
from datetime import datetime, timezone

st.set_page_config(page_title="Admin Review Queue — FoodLens AI", page_icon="🛡️", layout="wide")

CSS_PATH = Path(__file__).parent.parent / "assets" / "theme.css"
if CSS_PATH.exists():
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from db.session import SessionLocal
from db.models import Product, DataReport, ProductRevision
from foodlens.report_checks import validate_state_transition
from app.components.icons import get_icon_svg

ADMIN_SECRET = os.getenv("FOODLENS_ADMIN_PASSWORD_HASH", "foodlens_admin_secret")

# Admin Authentication Check
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

shield_icon = get_icon_svg("shield", size=24, color="#144730")

st.markdown(
    f"""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
        {shield_icon}
        <h1 style="margin: 0; color: #144730; font-size: 26px;">Admin Data Review Queue</h1>
    </div>
    """,
    unsafe_allow_html=True
)
st.caption("Review user-reported label inaccuracies, inspect image evidence, and publish verified product revisions.")

if not st.session_state.admin_authenticated:
    st.markdown("---")
    st.markdown("### 🔐 Admin Authentication Required")
    pwd_input = st.text_input("Enter Admin Password / Key", type="password")
    if st.button("Log In as Admin", type="primary"):
        if pwd_input == ADMIN_SECRET:
            st.session_state.admin_authenticated = True
            st.rerun()
        else:
            st.error("Invalid admin credentials.")
    st.stop()

# Logout button in top-right
col_top_l, col_top_r = st.columns([4, 1])
with col_top_r:
    if st.button("🚪 Log Out", width="stretch"):
        st.session_state.admin_authenticated = False
        st.rerun()

st.markdown("---")

db = SessionLocal()
try:
    # 1. Metrics Panel
    total_reps = db.query(DataReport).count()
    pending_reps = db.query(DataReport).filter(DataReport.status == "pending").count()
    approved_reps = db.query(DataReport).filter(DataReport.status == "approved").count()
    rejected_reps = db.query(DataReport).filter(DataReport.status == "rejected").count()
    rate = round((approved_reps / total_reps * 100.0), 1) if total_reps > 0 else 0.0

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Total Reports", total_reps)
    with m2:
        st.metric("Pending Review", pending_reps)
    with m3:
        st.metric("Approved & Published", approved_reps)
    with m4:
        st.metric("Rejected", rejected_reps)
    with m5:
        st.metric("Approval Rate", f"{rate}%")

    st.markdown("---")

    # 2. Queue Filters
    col_stat, col_fld = st.columns([2, 2])
    with col_stat:
        status_filter = st.selectbox(
            "Filter by Status",
            options=["All", "pending", "approved", "rejected", "needs_info", "duplicate"],
            index=1  # Default to 'pending'
        )
    with col_fld:
        field_filter = st.text_input("Filter by Field (e.g. protein_g, name)")

    query = db.query(DataReport)
    if status_filter != "All":
        query = query.filter(DataReport.status == status_filter)
    if field_filter and field_filter.strip():
        query = query.filter(DataReport.field.like(f"%{field_filter.strip()}%"))

    reports = query.order_by(DataReport.priority_score.desc(), DataReport.created_at.desc()).all()

    st.markdown(f"### 📋 Review Queue ({len(reports)} matching items)")

    if not reports:
        st.info("No reports found matching the selected filters.")
    else:
        for rep in reports:
            prod = rep.product
            prod_name = prod.name if prod else f"Product #{rep.product_id}"

            with st.container():
                st.markdown(
                    f"""
                    <div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 12px; padding: 14px 18px; margin-bottom: 14px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-weight: 700; font-size: 16px; color: #0F172A;">Report #{rep.id} — {prod_name}</span>
                            <span style="background: {'#FEF3C7' if rep.status=='pending' else '#DCFCE7' if rep.status=='approved' else '#FEE2E2'}; color: #0F172A; padding: 2px 10px; border-radius: 20px; font-size: 12px; font-weight: 700; text-transform: uppercase;">
                                {rep.status} • Priority: {rep.priority_score:.1f}
                            </span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                c_info, c_diff, c_actions = st.columns([1.5, 1.5, 1.2])

                with c_info:
                    st.write(f"**Target Field:** `{rep.field}`")
                    st.write(f"**Submitted At:** {rep.created_at.strftime('%Y-%m-%d %H:%M') if rep.created_at else 'Unknown'}")
                    if rep.comment:
                        st.info(f"💬 Reporter Note: {rep.comment}")
                    
                    if rep.auto_checks_json:
                        flags = rep.auto_checks_json.get("flags", [])
                        if flags:
                            st.warning(f"Auto-Check Notice: {', '.join(flags)}")
                        else:
                            st.caption("✓ Passed deterministic plausibility checks.")

                with c_diff:
                    st.markdown("**Comparison Diff:**")
                    st.markdown(
                        f"""
                        <div style="font-size: 13.5px; line-height: 1.6;">
                            🔴 <b>Current Value:</b> <code>{rep.current_value or 'None'}</code><br>
                            🟢 <b>Proposed Value:</b> <code>{rep.proposed_value}</code>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if rep.evidence_image_path and Path(rep.evidence_image_path).exists():
                        st.image(rep.evidence_image_path, caption="Uploaded Evidence", width=200)

                with c_actions:
                    note_input = st.text_input(
                        "Reviewer Note",
                        value=rep.reviewer_note or "",
                        key=f"note_{rep.id}",
                        placeholder="Reason for approval/rejection"
                    )

                    if rep.status in ("pending", "needs_info"):
                        b_app, b_rej = st.columns(2)
                        with b_app:
                            if st.button("✅ Approve", key=f"app_{rep.id}", type="primary", width="stretch"):
                                try:
                                    validate_state_transition(rep.status, "approved")
                                    # Write revision
                                    rev = ProductRevision(
                                        product_id=rep.product_id,
                                        field=rep.field,
                                        old_value=str(rep.current_value),
                                        new_value=str(rep.proposed_value),
                                        source="user_report",
                                        report_id=rep.id,
                                        changed_by="admin",
                                        changed_at=datetime.now(timezone.utc),
                                    )
                                    db.add(rev)

                                    # Update product in place
                                    if hasattr(prod, rep.field):
                                        setattr(prod, rep.field, rep.proposed_value)
                                    elif prod.nutrition and hasattr(prod.nutrition, rep.field):
                                        try:
                                            setattr(prod.nutrition, rep.field, float(rep.proposed_value))
                                        except ValueError:
                                            pass

                                    prod.verification_status = "admin_verified"
                                    rep.status = "approved"
                                    rep.reviewed_by = "admin"
                                    rep.reviewed_at = datetime.now(timezone.utc)
                                    rep.reviewer_note = note_input or "Approved by admin."
                                    db.commit()
                                    st.success("Approved and published revision!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")

                        with b_rej:
                            if st.button("❌ Reject", key=f"rej_{rep.id}", width="stretch"):
                                try:
                                    validate_state_transition(rep.status, "rejected")
                                    rep.status = "rejected"
                                    rep.reviewed_by = "admin"
                                    rep.reviewed_at = datetime.now(timezone.utc)
                                    rep.reviewer_note = note_input or "Rejected by admin."
                                    db.commit()
                                    st.warning("Report rejected.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                    else:
                        st.caption(f"Reviewed by {rep.reviewed_by} at {rep.reviewed_at.strftime('%Y-%m-%d %H:%M') if rep.reviewed_at else ''}")

                st.markdown("<hr style='border: none; border-top: 1px dashed #CBD5E1; margin: 12px 0;'>", unsafe_allow_html=True)
finally:
    db.close()
