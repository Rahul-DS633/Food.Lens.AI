"""
FoodLens AI — Settings, Privacy & Methodology
Features vector iconography, 3D card layout, and data management controls.
"""

import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st

st.set_page_config(page_title="Settings & Privacy — FoodLens AI", page_icon="🔍", layout="wide")

CSS_PATH = Path(__file__).parent.parent / "assets" / "theme.css"
if CSS_PATH.exists():
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.html(f"<style>{f.read()}</style>")

from db.session import SessionLocal
from db.models import Scan, XPEvent
from app.components.icons import get_icon_svg
from app.components.sidebar import render_sidebar
from app.components.page_header import render_page_header

render_sidebar("Settings")

render_page_header(
    title="Settings & Privacy Controls",
    subtitle="Configure dietary parameters, gamification options, and manage local data privacy.",
    icon_name="settings",
    overline="PREFERENCES & COMPLIANCE",
    action_pills=[
        {"icon": "shield", "text": "DPDP Act 2023"},
        {"icon": "lock", "text": "Local Storage"}
    ]
)

if "game_features_enabled" not in st.session_state:
    st.session_state.game_features_enabled = True

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Preferences")
    lang = st.radio("Language / भाषा", ["English (Default)", "हिंदी (Hindi)"], index=0 if st.session_state.get("language") == "en" else 1)
    st.session_state.language = "hi" if "हिंदी" in lang else "en"

    st.markdown("<hr style='border: none; border-top: 1.5px solid #E2E8F0; margin: 16px 0;'>", unsafe_allow_html=True)
    st.markdown("#### Dietary Profile & Allergens")
    st.markdown("Configure your allergies and demographic bands for personalized label evaluation.")
    if st.button("Manage Dietary Profile & Allergens →", type="primary", width="stretch"):
        st.switch_page("pages/7_Profile.py")

    st.markdown("<hr style='border: none; border-top: 1.5px solid #E2E8F0; margin: 16px 0;'>", unsafe_allow_html=True)
    st.markdown("#### Quest & Gamification Options")
    enable_game = st.toggle("Enable FoodLens Quest (XP, streaks, and badges)", value=st.session_state.game_features_enabled)
    st.session_state.game_features_enabled = enable_game
    if not enable_game:
        st.caption("Game features are hidden. Only pure nutrition calculation, OCR, and AI explanation will display.")

    st.markdown("<hr style='border: none; border-top: 1.5px solid #E2E8F0; margin: 16px 0;'>", unsafe_allow_html=True)
    st.markdown("#### Data Privacy & Local Storage")
    st.markdown("FoodLens stores minimal data locally in SQLite. Zero tracking, zero telemetry, full offline functionality.")
    if st.button("Clear Scan History & Reset Quest Progress", type="secondary", width="stretch"):
        db = SessionLocal()
        try:
            db.query(Scan).delete()
            db.query(XPEvent).delete()
            db.commit()
            st.success("History and progress cleared successfully!")
        finally:
            db.close()

with col2:
    st.markdown("#### Scientific Methodology & Architecture")
    st.markdown(
        """
        <div class="foodlens-card-3d">
            <h4 style="color: #144730; margin-top: 0; font-size: 16px;">Our 6 Core Architectural Principles</h4>
            <ol style="font-size: 13px; line-height: 1.6; color: #334155; padding-left: 18px; margin-bottom: 16px;">
                <li><b>Deterministic code calculates:</b> Pure Python arithmetic. Never ask or allow an LLM to calculate numbers.</li>
                <li><b>Never invent or zero-fill:</b> Missing nutrients remain <code>None</code>. Never assumed to be zero.</li>
                <li><b>Provenance & Confidence:</b> Every value tracks its origin (API, OCR, manual, user) and confidence.</li>
                <li><b>Neutral language:</b> No 'good/bad food' moralizing, no medical diagnosis, no disease claims.</li>
                <li><b>User correction agency:</b> You can always inspect, override, and correct extracted numbers.</li>
                <li><b>Safety-first gamification:</b> Rewards verified literacy and label reading. Never calorie restriction.</li>
            </ol>
            <h4 style="color: #DC2626; font-size: 14px; margin-bottom: 6px;">Safety & Health Notice</h4>
            <p style="font-size: 12px; color: #64748B; line-height: 1.5; margin: 0;">
                FoodLens AI is an academic food literacy tool. It is not an official FSSAI rating, medical diagnostic instrument, or clinical prescription.
                Allergen statements reflect text detected on packaging and do not guarantee facility cross-contact status.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
