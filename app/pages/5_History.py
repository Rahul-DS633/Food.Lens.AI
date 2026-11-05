"""
FoodLens AI — Scan History & Activity Log
"""

import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Scan History — FoodLens AI", page_icon="📜", layout="wide")

CSS_PATH = Path(__file__).parent.parent / "assets" / "theme.css"
if CSS_PATH.exists():
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from db.session import SessionLocal
from db.models import Scan, Product

st.title("📜 Scan History & Diary")
st.caption("Review your previously scanned packaged foods, verified labels, and category trends.")

db = SessionLocal()
try:
    scans = (
        db.query(Scan)
        .order_by(Scan.created_at.desc())
        .limit(30)
        .all()
    )

    if not scans:
        st.info("No scan history recorded yet. Open the Scanner to analyze your first packaged food!")
        if st.button("Start Scanning →"):
            st.switch_page("pages/1_Scan.py")
        st.stop()

    # Filter row
    cat_filter = st.selectbox("Filter by Category", ["All Categories", "biscuits", "snacks", "drinks", "spreads", "instant_noodles"])

    for s in scans:
        prod = s.product
        if not prod:
            continue

        if cat_filter != "All Categories" and prod.category != cat_filter:
            continue

        score_color = "#1B5E3F" if (s.score and s.score >= 70) else ("#F59E0B" if (s.score and s.score >= 45) else "#DC2626")
        time_str = s.created_at.strftime("%b %d, %Y • %I:%M %p") if s.created_at else "Recently"

        col1, col2, col3 = st.columns([1, 4, 1])

        with col1:
            st.markdown(
                f"""
                <div style="background: #F3F4F6; border-radius: 12px; height: 75px; display: flex; align-items: center; justify-content: center; font-size: 32px;">
                    {'🍪' if prod.category=='biscuits' else ('🍜' if 'noodle' in prod.category else ('🧃' if 'drink' in prod.category else '📦'))}
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                f"""
                <div style="font-size: 16px; font-weight: 800; color: #111827;">{prod.name}</div>
                <div style="font-size: 13px; color: #4B5563;"><b>{prod.brand}</b> • {prod.category.title()} • Barcode: <code>{prod.barcode}</code></div>
                <div style="font-size: 12px; color: #9CA3AF; margin-top: 2px;">{time_str} • Source: {s.source_type.upper()}</div>
                """,
                unsafe_allow_html=True
            )

        with col3:
            st.markdown(
                f"""
                <div style="text-align: right;">
                    <div style="font-size: 20px; font-weight: 800; color: {score_color};">{s.score or 'N/A'}/100</div>
                    <span style="font-size: 11px; padding: 2px 6px; border-radius: 6px; background: #F3F4F6; color: #6B7280;">Grade {prod.quality_grade or 'B'}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button("Inspect", key=f"reinspect_{s.id}", use_container_width=True):
                st.session_state.current_scan_product_id = prod.id
                st.switch_page("pages/2_Result.py")

        st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid #F3F4F6;'>", unsafe_allow_html=True)

finally:
    db.close()
