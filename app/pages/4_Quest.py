"""
FoodLens AI — FoodLens Quest & Mini-Games Hub
Gamified nutritional literacy: XP, streak protection, achievements, and educational mini-games.
"""

import streamlit as st
from datetime import date
from pathlib import Path

st.set_page_config(page_title="FoodLens Quest — Gamified Literacy", page_icon="🏆", layout="wide")

CSS_PATH = Path(__file__).parent.parent / "assets" / "theme.css"
if CSS_PATH.exists():
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from db.session import SessionLocal
from db.models import User, UserProgress, Achievement, UserAchievement, Product, XPEvent
from foodlens.gamification.xp import get_level_for_xp, calculate_xp_award
from foodlens.gamification.challenges import (
    get_daily_challenge, evaluate_sugar_guess, evaluate_serving_trap_answer
)
from app.components.xp_bar import render_xp_header
from app.components.badge import render_badge_card

st.title("🏆 FoodLens Quest")
st.caption("Learn to decode packaged food labels, protect your streak, and earn XP through verified knowledge.")

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

    # Tabs: Mini-Games, Badge Shelf, Daily Quests, Literacy Principles
    tab_games, tab_badges, tab_quests = st.tabs([
        "🎮 Literacy Mini-Games", "🏅 Badge Shelf", "📜 Today's Quests & Stamps"
    ])

    with tab_games:
        st.subheader("Interactive Food Literacy Challenges")

        game_choice = st.radio(
            "Choose a Mini-Game:",
            ["1. Guess Before You Scan (Sugar Spotter)", "2. The Serving Trap Quiz"],
            horizontal=True
        )

        st.markdown("---")

        if "1. Guess Before You Scan" in game_choice:
            st.markdown(
                """
                ### 🍭 Mini-Game 1: Guess Before You Scan
                Can you guess how many grams of sugar are in **1 serving** of these popular biscuits or drinks?
                *Closer guesses earn more XP (+10 to +25 XP)!*
                """
            )

            # Pick a sample item
            sample_product = db.query(Product).filter(Product.barcode == "8901719101052").first()  # Parle-G
            serving_size = sample_product.serving_size_g or 21.6
            actual_sugar = round(26.5 * (serving_size / 100.0), 1)  # ~5.7g sugar per serving

            st.info(f"**Item:** {sample_product.name} ({sample_product.brand}) • **1 Serving Size:** {serving_size} g")

            guess = st.slider("Your Guess: Grams of sugar in 1 serving", min_value=0.0, max_value=30.0, value=2.0, step=0.5)

            if st.button("Reveal the Truth! 🔍", type="primary"):
                xp_gain, msg = evaluate_sugar_guess(actual_sugar, guess)
                if xp_gain == 25:
                    st.success(msg)
                elif xp_gain == 15:
                    st.info(msg)
                else:
                    st.warning(msg)

                # Show sugar cubes
                tsps = round(actual_sugar / 4.0, 1)
                st.markdown(f"**Actual Sugar:** {actual_sugar} g (~{tsps} teaspoons)")

                progress.xp += xp_gain
                db.add(XPEvent(user_id=1, event_type="minigame_guess_sugar", xp=xp_gain, ref_id=str(actual_sugar)))
                db.commit()
                st.balloons()

        else:
            st.markdown(
                """
                ### 🕵️ Mini-Game 2: The Serving Trap Quiz
                Many snack packets look like single-portion snacks, but contain 2 to 4 servings according to the manufacturer label!
                """
            )
            # Maggi or Bhujia
            quiz_prod = db.query(Product).filter(Product.barcode == "8904063200142").first() # Haldiram's Bhujia 150g
            net_wt = quiz_prod.net_weight_g or 150.0
            serv_sz = quiz_prod.serving_size_g or 30.0
            actual_servings = round(net_wt / serv_sz, 1)  # 5.0 servings!

            st.markdown(f"**Product:** {quiz_prod.name} ({quiz_prod.brand}) — Net Weight: **{net_wt:g} g**")
            st.markdown("Look at this bag. How many manufacturer servings are packed inside?")

            chosen_servings = st.radio("Select how many servings you think this bag contains:", [1.0, 2.0, 3.0, 5.0], horizontal=True)

            if st.button("Check Answer! 🔎", type="primary"):
                xp_gain, msg = evaluate_serving_trap_answer(actual_servings, chosen_servings)
                if xp_gain == 20:
                    st.success(msg)
                else:
                    st.warning(msg)

                st.markdown(
                    f"""
                    **The Trap Explained:** Each declared serve is only {serv_sz}g, meaning this single bag contains **{actual_servings} full servings**.
                    If you eat the entire packet, you consume **{actual_servings}x** the calories, fat, and sodium listed in the single-serve column!
                    """
                )
                progress.xp += xp_gain
                db.add(XPEvent(user_id=1, event_type="minigame_serving_trap", xp=xp_gain, ref_id=str(actual_servings)))
                db.commit()

    with tab_badges:
        st.subheader("Achievement Badges")
        st.caption("Earn badges by scanning, verifying data, comparing foods, and discovering nutritional truths.")

        all_achievements = db.query(Achievement).all()
        earned_ids = {ua.achievement_id for ua in user.achievements} if user.achievements else set()

        # Display in a 3-column responsive grid
        cols = st.columns(3)
        for idx, a in enumerate(all_achievements):
            with cols[idx % 3]:
                is_earned = a.id in earned_ids
                render_badge_card({
                    "title": a.title,
                    "description": a.description,
                    "icon": a.icon,
                    "unlocked": is_earned
                })

    with tab_quests:
        st.subheader("Daily Literacy Quest & Category Stamps")
        today_quest = get_daily_challenge(date.today())

        st.markdown(
            f"""
            <div class="foodlens-card" style="border-left: 5px solid #1B5E3F;">
                <h4 style="margin: 0; color: #1B5E3F;">{today_quest['title']} (+{today_quest['xp_reward']} XP)</h4>
                <p style="margin: 6px 0; color: #4B5563;">{today_quest['description']}</p>
                <span class="pill-badge pill-xp">Active Today: {today_quest['date']}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("#### Category Stamps Collected")
        st.caption("Scan at least one product from each core Indian grocery category:")

        stamps = [
            ("Biscuits", "🍪", True),
            ("Instant Noodles", "🍜", True),
            ("Namkeen / Savory", "🌶️", True),
            ("Dairy / Spreads", "🧈", True),
            ("Beverages", "🧃", True),
            ("Breakfast Cereals", "🥣", False),
        ]

        stamp_cols = st.columns(len(stamps))
        for idx, (cat, emoji, collected) in enumerate(stamps):
            with stamp_cols[idx]:
                st.markdown(
                    f"""
                    <div style="text-align: center; padding: 12px; background: {'#F0FDF4' if collected else '#F9FAFB'}; border: 1.5px dashed {'#86EFAC' if collected else '#D1D5DB'}; border-radius: 12px;">
                        <div style="font-size: 28px;">{emoji}</div>
                        <div style="font-weight: 700; font-size: 12px; margin-top: 4px;">{cat}</div>
                        <div style="font-size: 10px; color: {'#166534' if collected else '#9CA3AF'}; font-weight: 700;">
                            {'✓ STAMPED' if collected else 'UNSTAMPED'}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

finally:
    db.close()
