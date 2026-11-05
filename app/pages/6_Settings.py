"""
FoodLens AI — Settings, Privacy & Methodology
"""

import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Settings & Privacy — FoodLens AI", page_icon="⚙️", layout="wide")

CSS_PATH = Path(__file__).parent.parent / "assets" / "theme.css"
if CSS_PATH.exists():
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from db.session import SessionLocal
from db.models import User, Scan, XPEvent

st.title("⚙️ Settings & Privacy Controls")

if "game_features_enabled" not in st.session_state:
    st.session_state.game_features_enabled = True

col1, col2 = st.columns(2)

with col1:
    st.subheader("🌐 Preferences")
    lang = st.radio("Language / भाषा", ["English (Default)", "हिंदी (Hindi)"], index=0 if st.session_state.get("language")=="en" else 1)
    st.session_state.language = "hi" if "हिंदी" in lang else "en"

    st.markdown("---")
    st.subheader("🎮 Quest & Gamification Options")
    enable_game = st.toggle("Enable FoodLens Quest (XP, streaks, and badges)", value=st.session_state.game_features_enabled)
    st.session_state.game_features_enabled = enable_game
    if not enable_game:
        st.caption("Game features are hidden. Only pure nutrition calculation, OCR, and AI explanation will display.")

    st.markdown("---")
    st.subheader("🛡️ Data Privacy & Account")
    st.markdown("FoodLens stores minimal data locally in SQLite. No tracking or telemetry.")
    if st.button("🗑️ Clear Scan History & Reset Quest Progress", type="secondary"):
        db = SessionLocal()
        try:
            db.query(Scan).delete()
            db.query(XPEvent).delete()
            db.commit()
            st.success("History and progress cleared successfully!")
        finally:
            db.close()

with col2:
    st.subheader("📖 Scientific Methodology & Disclaimers")
    st.markdown(
        """
        <div class="foodlens-card">
            <h4 style="color: #1B5E3F; margin-top: 0;">Our 6 Core Architectural Principles</h4>
            <ol style="font-size: 13px; line-height: 1.6; color: #374151; padding-left: 18px;">
                <li><b>Deterministic code calculates:</b> The language model only explains validated data. Calculations are 100% Python code.</li>
                <li><b>Never invent or zero-fill:</b> Missing nutrients remain <code>None</code>. Never assumed to be zero.</li>
                <li><b>Provenance & Confidence:</b> Every number carries its source (API, OCR, manual, user) and confidence.</li>
                <li><b>Neutral language:</b> No 'good food / bad food', no medical diagnosis, no disease claims.</li>
                <li><b>User correction agency:</b> You can always inspect and edit OCR extractions.</li>
                <li><b>Safety-first gamification:</b> Rewards label reading and knowledge. Never rewards calorie restriction.</li>
            </ol>
            <h4 style="color: #DC2626;">Regulatory & Safety Disclaimer</h4>
            <p style="font-size: 12px; color: #4B5563; line-height: 1.5;">
                • FoodLens AI is an academic prototype for food literacy and education.<br>
                • It is <b>not</b> an official FSSAI rating, medical diagnostic tool, or clinical prescription.<br>
                • The nutritional score evaluates macro balance only; it says nothing about microbiological safety, contamination, or product expiry.<br>
                • Allergen statements indicate text detected on packaging, never a guarantee of facility cross-contact safety.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
