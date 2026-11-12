"""
FoodLens AI — Scan History & Activity Log
Features realistic product thumbnails, vector status badges, and 3D card layout.
"""

import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st

st.set_page_config(page_title="Scan History — FoodLens AI", page_icon="🔍", layout="wide")

CSS_PATH = Path(__file__).parent.parent / "assets" / "theme.css"
if CSS_PATH.exists():
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from db.session import SessionLocal
from db.models import Scan
from app.components.icons import get_icon_svg
from app.components.images import get_product_image
from app.components.report_modal import render_report_issue_dialog
from app.components.sidebar import render_sidebar
from app.components.page_header import render_page_header

render_sidebar("History")

render_page_header(
    title="Scan History & Product Diary",
    subtitle="Review your previously scanned packaged foods, verified labels, and nutritional scores.",
    icon_name="history",
    overline="PRODUCT DIARY & ARCHIVE",
    action_pills=[
        {"icon": "history", "text": "Local Archive"},
        {"icon": "shield", "text": "Zero Telemetry"}
    ]
)

db = SessionLocal()
try:
    scans = (
        db.query(Scan)
        .order_by(Scan.created_at.desc())
        .limit(30)
        .all()
    )

    if not scans:
        history_empty_html = (
            f'<div style="background: #F8FAFC; border: 1.5px dashed #CBD5E1; border-radius: 16px; padding: 36px 24px; text-align: center; margin: 16px 0 24px 0;">'
            f'<div style="font-size: 38px; margin-bottom: 10px;">🧺</div>'
            f'<h3 style="color: #144730; margin: 0 0 6px 0; font-size: 19px; font-weight: 700;">No Scan History Recorded Yet</h3>'
            f'<p style="color: #475569; font-size: 14.5px; max-width: 500px; margin: 0 auto; line-height: 1.5;">'
            f'You haven\'t scanned any packaged foods yet. Point your camera at a food label or explore sample products to build your verified product diary.'
            f'</p>'
            f'</div>'
        )
        if hasattr(st, "html"):
            st.markdown(history_empty_html)
        else:
            st.markdown(history_empty_html, unsafe_allow_html=True)

        if st.button("Start Scanning →", width="stretch", type="primary"):
            st.switch_page("pages/1_Scan.py")
        st.stop()

    cat_filter = st.selectbox("Filter by Category", ["All Categories", "biscuits", "snacks", "drinks", "spreads", "instant_noodles"])

    for s in scans:
        prod = s.product
        if not prod:
            continue

        if cat_filter != "All Categories" and prod.category != cat_filter:
            continue

        score_color = "#166534" if (s.score and s.score >= 70) else ("#D97706" if (s.score and s.score >= 45) else "#DC2626")
        time_str = s.created_at.strftime("%b %d, %Y • %I:%M %p") if s.created_at else "Recently"
        img_uri = get_product_image(prod.name, prod.brand, prod.category, prod.image_url)

        col1, col2, col3 = st.columns([1, 4, 1.2])

        with col1:
            st.markdown(
                f"""
                <div style="width: 100%; height: 75px; border-radius: 12px; overflow: hidden; background: #FFFFFF; border: 1px solid #E2E8F0; box-shadow: 0 2px 6px rgba(0,0,0,0.04); display: flex; align-items: center; justify-content: center; padding: 4px;">
                    <img src="{img_uri}" alt="{prod.name}" style="max-width: 100%; max-height: 100%; object-fit: contain;">
                </div>
                """,
                unsafe_allow_html=True,
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                f"""
                <div style="font-size: 15.5px; font-weight: 800; color: #0F172A; margin-bottom: 2px;">{prod.name}</div>
                <div style="font-size: 13px; color: #475569;">
                    <b>{prod.brand}</b> • <span style="text-transform: capitalize;">{prod.category}</span> • 
                    <code>{prod.barcode}</code>
                </div>
                <div style="font-size: 11.5px; color: #64748B; margin-top: 3px;">{time_str} • Source: {s.source_type.upper()}</div>
                """,
                unsafe_allow_html=True
            )

        with col3:
            st.markdown(
                f"""
                <div style="text-align: right; margin-bottom: 6px;">
                    <span style="font-size: 20px; font-weight: 800; color: {score_color}; font-family: 'JetBrains Mono', monospace;">
                        {s.score or 'N/A'}<span style="font-size: 12px; color: #64748B;">/100</span>
                    </span>
                    <span style="font-size: 11px; font-weight: 700; padding: 2px 7px; border-radius: 6px; background: #F1F5F9; color: #475569; margin-left: 4px;">
                        Grade {prod.quality_grade or 'B'}
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button("Inspect", key=f"reinspect_{s.id}", width="stretch"):
                st.session_state.current_scan_product_id = prod.id
                st.switch_page("pages/2_Result.py")

        render_report_issue_dialog(prod.id, prod.name, key_suffix=f"hist_{s.id}")
        st.markdown("<hr style='margin: 10px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

finally:
    db.close()
