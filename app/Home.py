"""
FoodLens AI — Home & Quick Scanner Hub
Features interactive 3D WebGL Three.js hero, vector icon system,
and realistic packaged food visual showcase.
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so 'db' and 'foodlens' packages resolve
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st
from datetime import date

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
from db.models import User, Product
from foodlens.gamification.xp import get_level_for_xp
from foodlens.gamification.challenges import get_daily_challenge
from app.components.xp_bar import render_xp_header
from app.components.icons import get_icon_svg, icon_badge
from app.components.images import get_product_image
from app.components.three_d import render_3d_hero

# Initialize session state variables
if "user_id" not in st.session_state:
    st.session_state.user_id = 1
if "language" not in st.session_state:
    st.session_state.language = "en"
if "current_scan_product_id" not in st.session_state:
    st.session_state.current_scan_product_id = None
if "active_scan_tab" not in st.session_state:
    st.session_state.active_scan_tab = "camera"

# Display feedback toast if coming from Profile save
if st.session_state.get("profile_saved_toast"):
    st.toast("🎉 Dietary profile saved! Personalized Food Fit is now active for all scans.", icon="🛡️")
    st.session_state["profile_saved_toast"] = False

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

    # 1. Render Header XP & Streak Bar
    render_xp_header(
        xp=xp,
        level=lvl_name,
        level_icon=lvl_icon,
        base_xp=base_xp,
        next_xp=next_xp,
        current_streak=streak,
        streak_freezes=freezes
    )

    # 2. Interactive Three.js 3D WebGL Hero Canvas
    render_3d_hero(height=230)

    # 3. Hero Title & Language Switcher
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        sparkle_icon = get_icon_svg("sparkles", size=18, color="#1B5E3F")
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 8px; margin-top: 10px;">
                <span class="pill-badge pill-xp" style="margin-bottom: 2px;">
                    {sparkle_icon} Grounded Food Intelligence
                </span>
            </div>
            <h1 style="color: #144730; margin: 4px 0 6px 0; font-size: 32px;">FoodLens AI</h1>
            <p style="font-size: 15.5px; color: #475569; line-height: 1.5; margin-bottom: 16px;">
                Point your camera at any packaged food and discover what is <i>really</i> inside —
                with 100% deterministic arithmetic and every single number traceable to its label source.
            </p>
            """,
            unsafe_allow_html=True
        )
    with col_t2:
        lang = st.radio("Language / भाषा", ["English", "हिंदी"], horizontal=True, label_visibility="collapsed")
        st.session_state.language = "hi" if lang == "हिंदी" else "en"

    # 4. Today's Quest Card
    today_quest = get_daily_challenge(date.today())
    trophy_icon = get_icon_svg("trophy", size=22, color="#166534")
    st.markdown(
        f"""
        <div class="foodlens-card-3d" style="background: linear-gradient(90deg, #F0FDF4 0%, #ECFCCB 100%); border: 1.5px solid #86EFAC; margin-bottom: 22px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 14px;">
                    <div style="width: 46px; height: 46px; border-radius: 12px; background: rgba(255,255,255,0.8); display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
                        {trophy_icon}
                    </div>
                    <div>
                        <span style="background: #1B5E3F; color: #FFFFFF !important; font-size: 11px; font-weight: 800; padding: 3px 8px; border-radius: 6px; letter-spacing: 0.5px;">
                            DAILY QUEST
                        </span>
                        <h3 style="margin: 4px 0 2px 0; color: #166534; font-size: 17px;">{today_quest['title']}</h3>
                        <div style="color: #374151; font-size: 13.5px;">{today_quest['description']}</div>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 22px; font-weight: 800; color: #1B5E3F; font-family: 'JetBrains Mono', monospace;">+{today_quest['xp_reward']} XP</div>
                    <span style="font-size: 12px; font-weight: 600; color: #475569;">Literacy Reward</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 5. Quick Action Columns (3D Elevating Cards with Vector Badges)
    col1, col2, col3 = st.columns(3)

    cam_badge = icon_badge("camera", bg="#DCFCE7", color="#166534", size=24, badge_size=48)
    scale_badge = icon_badge("scale", bg="#EFF6FF", color="#2563EB", size=24, badge_size=48)
    game_badge = icon_badge("gamepad", bg="#FDF4FF", color="#9333EA", size=24, badge_size=48)

    with col1:
        st.markdown(
            f"""
            <div class="action-card-3d">
                <div style="margin-bottom: 12px;">{cam_badge}</div>
                <h3 style="color: #144730; margin: 0 0 6px 0; font-size: 18px;">Scan a Food</h3>
                <p style="font-size: 13.5px; color: #475569; min-height: 42px; line-height: 1.4;">
                    Multi-angle camera capture, photo uploads & OCR label verification with INS ingredient mapping.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Open Scanner →", width="stretch", type="primary"):
            st.switch_page("pages/1_Scan.py")

    with col2:
        st.markdown(
            f"""
            <div class="action-card-3d">
                <div style="margin-bottom: 12px;">{scale_badge}</div>
                <h3 style="color: #144730; margin: 0 0 6px 0; font-size: 18px;">Compare Foods</h3>
                <p style="font-size: 13.5px; color: #475569; min-height: 42px; line-height: 1.4;">
                    Side-by-side per-100g nutritional evaluation to spot hidden sugars, saturated fats, and sodium.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Compare Snacks →", width="stretch"):
            st.switch_page("pages/3_Compare.py")

    with col3:
        st.markdown(
            f"""
            <div class="action-card-3d">
                <div style="margin-bottom: 12px;">{game_badge}</div>
                <h3 style="color: #144730; margin: 0 0 6px 0; font-size: 18px;">FoodLens Quest</h3>
                <p style="font-size: 13.5px; color: #475569; min-height: 42px; line-height: 1.4;">
                    Guess Before You Scan mini-game, Serving Trap quiz, streak protection, and milestone badges.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Play Mini-Games →", width="stretch"):
            st.switch_page("pages/4_Quest.py")

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # 6. Realistic Packaged Food Visual Showcase (Instant Demos)
    bolt_icon = get_icon_svg("bolt", size=22, color="#EA580C")
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
            {bolt_icon}
            <h2 style="color: #144730; margin: 0; font-size: 22px;">Verified Indian Products (Instant 1-Click Inspection)</h2>
        </div>
        <p style="color: #64748B; font-size: 14px; margin-bottom: 16px;">
            Select any popular packaged item below to view authentic packaging photography, live portion calculation, 3D sugar cubes, and grounded AI analysis:
        </p>
        """,
        unsafe_allow_html=True
    )

    preseeded_prods = db.query(Product).limit(5).all()
    demo_cols = st.columns(len(preseeded_prods))

    for idx, p in enumerate(preseeded_prods):
        img_uri = get_product_image(p.name, p.brand, p.category, p.image_url)
        n = p.nutrition
        cals = f"{n.energy_kcal:g} kcal" if (n and n.energy_kcal) else "N/A"
        sugars = f"{n.sugars_g:g}g sugar" if (n and n.sugars_g is not None) else ""

        with demo_cols[idx]:
            st.markdown(
                f"""
                <div class="product-card-3d" style="padding: 12px; text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div style="width: 100%; height: 130px; border-radius: 12px; overflow: hidden; background: #F8FAFC; margin-bottom: 10px; border: 1px solid #E2E8F0; display: flex; align-items: center; justify-content: center;">
                            <img src="{img_uri}" alt="{p.name}" style="width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s ease;">
                        </div>
                        <div style="display: flex; justify-content: center; gap: 4px; margin-bottom: 6px;">
                            <span style="font-size: 10.5px; font-weight: 700; padding: 2px 7px; border-radius: 6px; background: #DCFCE7; color: #166534; text-transform: uppercase;">
                                {p.brand}
                            </span>
                            <span style="font-size: 10.5px; font-weight: 600; padding: 2px 6px; border-radius: 6px; background: #F1F5F9; color: #475569;">
                                {p.category}
                            </span>
                        </div>
                        <div style="font-weight: 800; font-size: 13.5px; color: #0F172A; line-height: 1.3; min-height: 36px; margin-bottom: 8px;">
                            {p.name}
                        </div>
                        <div style="font-size: 11.5px; color: #64748B; margin-bottom: 10px;">
                            <b style="color: #0F172A;">{cals}</b> {f'• {sugars}' if sugars else ''}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button(f"Inspect {p.brand}", key=f"demo_btn_{p.id}", width="stretch"):
                st.session_state.current_scan_product_id = p.id
                st.switch_page("pages/2_Result.py")

finally:
    db.close()
