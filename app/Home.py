"""
FoodLens AI — Home & Quick Scanner
"""

import streamlit as st
from datetime import date
from pathlib import Path

# Setup page configuration
st.set_page_config(
    page_title="FoodLens AI — Food Intelligence",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load theme CSS
CSS_PATH = Path(__file__).parent / "assets" / "theme.css"
if CSS_PATH.exists():
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from db.session import SessionLocal
from db.models import User, UserProgress, Scan, Product
from foodlens.gamification.xp import get_level_for_xp
from foodlens.gamification.challenges import get_daily_challenge
from app.components.xp_bar import render_xp_header

# Initialize session state variables
if "user_id" not in st.session_state:
    st.session_state.user_id = 1
if "language" not in st.session_state:
    st.session_state.language = "en"
if "current_scan_product_id" not in st.session_state:
    st.session_state.current_scan_product_id = None
if "active_scan_tab" not in st.session_state:
    st.session_state.active_scan_tab = "camera"

# Fetch user progress from DB
db = SessionLocal()
try:
    user = db.query(User).filter(User.id == st.session_state.user_id).first()
    progress = user.progress if user else None
    xp = progress.xp if progress else 25
    level = progress.level if progress else "Label Rookie"
    streak = progress.current_streak if progress else 1
    freezes = progress.streak_freezes if progress else 1

    lvl_name, lvl_icon, base_xp, next_xp = get_level_for_xp(xp)

    # Render Header XP & Streak Bar
    render_xp_header(
        xp=xp,
        level=lvl_name,
        level_icon=lvl_icon,
        base_xp=base_xp,
        next_xp=next_xp,
        current_streak=streak,
        streak_freezes=freezes
    )

    # Hero Title & Pitch
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.markdown(
            """
            <h1 style="color: #1B5E3F; margin-bottom: 2px;">FoodLens AI</h1>
            <p style="font-size: 16px; color: #4B5563;">
                Point your camera at any packaged food and discover what is <i>really</i> inside —
                with every single number traceable to its source.
            </p>
            """,
            unsafe_allow_html=True
        )
    with col_t2:
        lang = st.radio("Language / भाषा", ["English", "हिंदी"], horizontal=True, label_visibility="collapsed")
        st.session_state.language = "hi" if lang == "हिंदी" else "en"

    st.markdown("---")

    # Today's Quest Card
    today_quest = get_daily_challenge(date.today())
    st.markdown(
        f"""
        <div class="foodlens-card" style="background: linear-gradient(90deg, #F0FDF4 0%, #ECFCCB 100%); border: 1.5px solid #86EFAC;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="background: #1B5E3F; color: white; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 6px;">
                        TODAY'S QUEST
                    </span>
                    <h3 style="margin: 6px 0 2px 0; color: #166534;">{today_quest['title']}</h3>
                    <div style="color: #374151; font-size: 14px;">{today_quest['description']}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 20px; font-weight: 800; color: #1B5E3F;">+{today_quest['xp_reward']} XP</div>
                    <span style="font-size: 12px; color: #4B5563;">Literacy Reward</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Quick Action Columns
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="foodlens-card">
                <div style="font-size: 32px;">📸</div>
                <h3 style="color: #1B5E3F; margin-top: 8px;">Scan a Food</h3>
                <p style="font-size: 13px; color: #6B7280;">Use your camera or upload barcode & label photos with OCR verification.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Open Scanner →", use_container_width=True, type="primary"):
            st.switch_page("pages/1_Scan.py")

    with col2:
        st.markdown(
            """
            <div class="foodlens-card">
                <div style="font-size: 32px;">⚖️</div>
                <h3 style="color: #1B5E3F; margin-top: 8px;">Compare Foods</h3>
                <p style="font-size: 13px; color: #6B7280;">Side-by-side per-100g comparison to find hidden sugars and better options.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Compare Snacks →", use_container_width=True):
            st.switch_page("pages/3_Compare.py")

    with col3:
        st.markdown(
            """
            <div class="foodlens-card">
                <div style="font-size: 32px;">🎮</div>
                <h3 style="color: #1B5E3F; margin-top: 8px;">FoodLens Quest</h3>
                <p style="font-size: 13px; color: #6B7280;">Guess Before You Scan mini-game, Serving Trap quiz, and unlock badges.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Play Mini-Games →", use_container_width=True):
            st.switch_page("pages/4_Quest.py")

    # One-Click Instant Demos (Pre-seeded Verified Indian Products)
    st.subheader("⚡ Instant Demo Products (1-Click Inspection)")
    st.caption("Click any packaged item below to see instant deterministic calculation, sugar cubes, and grounded AI:")

    preseeded_prods = db.query(Product).limit(5).all()
    demo_cols = st.columns(len(preseeded_prods))

    for idx, p in enumerate(preseeded_prods):
        with demo_cols[idx]:
            st.markdown(f"**{p.brand}**")
            st.caption(p.name)
            if st.button(f"Inspect {p.brand}", key=f"demo_btn_{p.id}", use_container_width=True):
                st.session_state.current_scan_product_id = p.id
                st.switch_page("pages/2_Result.py")

finally:
    db.close()
