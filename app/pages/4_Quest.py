"""
FoodLens AI — FoodLens Quest & Gamified Literacy Hub
Features realistic product visuals in mini-games, 3D sugar cubes,
vector achievement badges, and interactive literacy challenges.
"""

import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st
from datetime import date

st.set_page_config(page_title="FoodLens Quest — Food Intelligence", page_icon="🔍", layout="wide")

CSS_PATH = Path(__file__).parent.parent / "assets" / "theme.css"
if CSS_PATH.exists():
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from db.session import SessionLocal
from db.models import User, Achievement, UserAchievement, Product, XPEvent
from foodlens.gamification.xp import get_level_for_xp
from foodlens.gamification.challenges import (
    get_daily_challenge, evaluate_sugar_guess, evaluate_serving_trap_answer
)
from app.components.xp_bar import render_xp_header
from app.components.badge import render_badge_card
from app.components.icons import get_icon_svg
from app.components.images import get_product_image
from app.components.sugar_cubes import render_sugar_cubes
from app.components.sidebar import render_sidebar
from app.components.page_header import render_page_header

render_sidebar("Quest")

render_page_header(
    title="FoodLens Quest & Literacy Hub",
    subtitle="Learn to decode packaged food labels, protect your streak, and earn XP through verified knowledge.",
    icon_name="trophy",
    overline="GAMIFIED FOOD LITERACY",
    action_pills=[
        {"icon": "trophy", "text": "Daily Quests"},
        {"icon": "flame", "text": "Streak Shields"}
    ]
)

db = SessionLocal()
try:
    user = db.query(User).filter(User.id == 1).first()
    progress = user.progress if user else None
    xp = progress.xp if progress else 25
    streak = progress.current_streak if progress else 1
    freezes = progress.streak_freezes if progress else 1

    lvl_name, lvl_icon, base_xp, next_xp = get_level_for_xp(xp)

    # Top Status Bar
    render_xp_header(
        xp=xp,
        level=lvl_name,
        level_icon=lvl_icon,
        base_xp=base_xp,
        next_xp=next_xp,
        current_streak=streak,
        streak_freezes=freezes
    )

    # Tabs: Mini-Games, Badge Shelf, Daily Quests
    tab_games, tab_badges, tab_quests = st.tabs([
        "Literacy Mini-Games", "Badge Shelf", "Today's Quests & Stamps"
    ])

    with tab_games:
        st.markdown("### Interactive Food Literacy Challenges")

        game_choice = st.radio(
            "Choose a Mini-Game:",
            ["1. Guess Before You Scan (Sugar Spotter)", "2. The Serving Trap Quiz"],
            horizontal=True
        )

        st.markdown("<hr style='border: none; border-top: 1.5px solid #E2E8F0; margin: 16px 0;'>", unsafe_allow_html=True)

        if "1. Guess Before You Scan" in game_choice:
            sample_product = db.query(Product).filter(Product.barcode == "8901719101052").first()  # Parle-G
            serving_size = sample_product.serving_size_g or 21.6
            actual_sugar = round(26.5 * (serving_size / 100.0), 1)  # ~5.7g sugar per serving
            img_uri = get_product_image(sample_product.name, sample_product.brand, sample_product.category, sample_product.image_url)

            col_g1, col_g2 = st.columns([1, 2])
            with col_g1:
                st.markdown(
                    f"""
                    <div class="product-card-3d" style="padding: 14px; text-align: center;">
                        <div style="width: 100%; height: 160px; border-radius: 12px; overflow: hidden; background: #FFFFFF; border: 1px solid #E2E8F0; margin-bottom: 8px; display: flex; align-items: center; justify-content: center; padding: 6px;">
                            <img src="{img_uri}" alt="{sample_product.name}" style="max-width: 100%; max-height: 100%; object-fit: contain;">
                        </div>
                        <div style="font-weight: 800; font-size: 14px; color: #0F172A;">{sample_product.name}</div>
                        <div style="font-size: 12px; color: #64748B;">1 Serving = <b>{serving_size:g} g</b> (~4 biscuits)</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col_g2:
                cubes_icon = get_icon_svg("cubes", size=20, color="#2563EB")
                st.markdown(
                    f"""
                    <div style="display: flex; align-items: center; gap: 8px;">
                        {cubes_icon}
                        <h4 style="margin: 0; color: #1E3A8A;">Mini-Game 1: Guess Before You Scan</h4>
                    </div>
                    <p style="font-size: 13.5px; color: #475569; margin: 6px 0 14px 0;">
                        How many grams of sugar do you think are hidden in just <b>1 standard serving ({serving_size:g}g)</b> of these biscuits?
                        Closer guesses earn more XP (+10 to +25 XP)!
                    </p>
                    """,
                    unsafe_allow_html=True
                )

                guess = st.slider("Your Guess: Grams of sugar in 1 serving", min_value=0.0, max_value=25.0, value=2.0, step=0.5)

                if st.button("Reveal the Truth! 🔍", type="primary", width="stretch"):
                    xp_gain, msg = evaluate_sugar_guess(actual_sugar, guess)
                    if xp_gain == 25:
                        st.success(msg)
                    elif xp_gain == 15:
                        st.info(msg)
                    else:
                        st.warning(msg)

                    render_sugar_cubes(actual_sugar, portion_label="1 serving")

                    progress.xp += xp_gain
                    db.add(XPEvent(user_id=1, event_type="minigame_guess_sugar", xp=xp_gain, ref_id=str(actual_sugar)))

                    # Award 'Sugar Spotter' badge for completing the sugar literacy mini-game
                    ach = db.query(Achievement).filter(Achievement.code == "SUGAR_SPOTTER").first()
                    if ach:
                        existing_ach = db.query(UserAchievement).filter(
                            UserAchievement.user_id == progress.user_id,
                            UserAchievement.achievement_id == ach.id
                        ).first()
                        if not existing_ach:
                            db.add(UserAchievement(user_id=progress.user_id, achievement_id=ach.id))

                    db.commit()

        else:
            quiz_prod = db.query(Product).filter(Product.barcode == "8904063200142").first() # Haldiram's Bhujia 150g
            net_wt = quiz_prod.net_weight_g or 150.0
            serv_sz = quiz_prod.serving_size_g or 30.0
            actual_servings = round(net_wt / serv_sz, 1)
            img_uri = get_product_image(quiz_prod.name, quiz_prod.brand, quiz_prod.category, quiz_prod.image_url)

            col_q1, col_q2 = st.columns([1, 2])
            with col_q1:
                st.markdown(
                    f"""
                    <div class="product-card-3d" style="padding: 14px; text-align: center;">
                        <div style="width: 100%; height: 160px; border-radius: 12px; overflow: hidden; background: #FFFFFF; border: 1px solid #E2E8F0; margin-bottom: 8px; display: flex; align-items: center; justify-content: center; padding: 6px;">
                            <img src="{img_uri}" alt="{quiz_prod.name}" style="max-width: 100%; max-height: 100%; object-fit: contain;">
                        </div>
                        <div style="font-weight: 800; font-size: 14px; color: #0F172A;">{quiz_prod.name}</div>
                        <div style="font-size: 12px; color: #64748B;">Total Net Weight: <b>{net_wt:g} g</b></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col_q2:
                scale_icon = get_icon_svg("scale", size=20, color="#1B5E3F")
                st.markdown(
                    f"""
                    <div style="display: flex; align-items: center; gap: 8px;">
                        {scale_icon}
                        <h4 style="margin: 0; color: #144730;">Mini-Game 2: The Serving Trap Quiz</h4>
                    </div>
                    <p style="font-size: 13.5px; color: #475569; margin: 6px 0 14px 0;">
                        Packaged snacks often look like single-portion bags, but contain multiple manufacturer servings.
                        How many official servings are packed inside this <b>{net_wt:g}g</b> packet?
                    </p>
                    """,
                    unsafe_allow_html=True
                )

                chosen_servings = st.radio("Select how many servings you think this bag contains:", [1.0, 2.0, 3.0, 5.0], horizontal=True)

                if st.button("Check Answer! 🔎", type="primary", width="stretch"):
                    xp_gain, msg = evaluate_serving_trap_answer(actual_servings, chosen_servings)
                    if xp_gain == 20:
                        st.success(msg)
                    else:
                        st.warning(msg)

                    st.markdown(
                        f"""
                        <div style="background: #F0FDF4; border: 1.5px solid #86EFAC; border-radius: 12px; padding: 14px 16px; margin-top: 10px; font-size: 13.5px; color: #166534;">
                            <b>The Serving Trap Explained:</b> Each manufacturer-declared serving is only {serv_sz}g, meaning this single pouch contains <b>{actual_servings} full servings</b>!
                            Eating the entire pouch delivers <b>{actual_servings}x</b> the sodium, saturated fat, and calories displayed in the per-serve table.
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    progress.xp += xp_gain
                    db.add(XPEvent(user_id=1, event_type="minigame_serving_trap", xp=xp_gain, ref_id=str(actual_servings)))
                    db.commit()

    with tab_badges:
        st.markdown("### Milestone & Literacy Badges")
        st.caption("Earn badges by scanning, verifying data, comparing foods, and discovering nutritional truths.")

        all_achievements = db.query(Achievement).all()
        earned_ids = {ua.achievement_id for ua in user.achievements} if user.achievements else set()

        b_cols = st.columns(3)
        for idx, ach in enumerate(all_achievements):
            with b_cols[idx % 3]:
                render_badge_card({
                    "code": ach.code,
                    "title": ach.title,
                    "description": ach.description,
                    "unlocked": ach.id in earned_ids
                })

    with tab_quests:
        st.markdown("### Today's Challenges & Daily Stamp")
        today_quest = get_daily_challenge(date.today())
        st.markdown(
            f"""
            <div class="foodlens-card-3d" style="background: linear-gradient(135deg, #F0FDF4 0%, #ECFCCB 100%); border: 1.5px solid #86EFAC; margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="background: #1B5E3F; color: #FFFFFF !important; font-size: 11px; font-weight: 800; padding: 3px 8px; border-radius: 6px;">
                            DAILY OBJECTIVE
                        </span>
                        <h3 style="margin: 6px 0 3px 0; color: #166534;">{today_quest['title']}</h3>
                        <div style="color: #374151; font-size: 14px;">{today_quest['description']}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 24px; font-weight: 800; color: #1B5E3F; font-family: 'JetBrains Mono', monospace;">+{today_quest['xp_reward']} XP</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="foodlens-card-3d" style="background: linear-gradient(135deg, #EFF6FF 0%, #E0F2FE 100%); border: 1.5px solid #93C5FD; margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="background: #0369A1; color: #FFFFFF !important; font-size: 11px; font-weight: 800; padding: 3px 8px; border-radius: 6px;">
                            COOPERATIVE FAMILY CHALLENGE
                        </span>
                        <h3 style="margin: 6px 0 3px 0; color: #075985;">The Family Pantry Audit</h3>
                        <div style="color: #334155; font-size: 14px;">Scan 5 packaged snacks together this week with your Family Profiles active to unlock shared dietary literacy.</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 24px; font-weight: 800; color: #0284C7; font-family: 'JetBrains Mono', monospace;">+25 XP</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="foodlens-card-3d" style="background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); border: 1.5px solid #FCD34D; margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="background: #92400E; color: #FFFFFF !important; font-size: 11px; font-weight: 800; padding: 3px 8px; border-radius: 6px;">
                            LITERACY CHALLENGE
                        </span>
                        <h3 style="margin: 6px 0 3px 0; color: #78350F;">Front-of-Pack Myth Buster</h3>
                        <div style="color: #451A03; font-size: 14px;">Inspect marketing claims against real nutrition numbers and ingredients to reveal verified label facts.</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 24px; font-weight: 800; color: #92400E; font-family: 'JetBrains Mono', monospace;">+15 XP</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

finally:
    db.close()
