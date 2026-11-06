"""
FoodLens AI — XP Bar & Level Tracker
Renders user rank, level progress bar, streak flame, and streak freeze indicators
using crisp vector SVG icons and a 3D glassmorphism status bar.
"""

import streamlit as st
from app.components.icons import get_icon_svg


def render_xp_header(
    xp: int,
    level: str,
    level_icon: str,
    base_xp: int,
    next_xp: int,
    current_streak: int,
    streak_freezes: int
):
    """
    Renders top gamification status bar with vector icons and modern gradient styling.
    """
    progress_ratio = 1.0 if next_xp <= base_xp else min(1.0, max(0.0, (xp - base_xp) / (next_xp - base_xp)))

    flame_svg = get_icon_svg("flame", size=18, color="#F59E0B", filled=True)
    shield_svg = get_icon_svg("shield", size=18, color="#60A5FA", filled=True)
    trophy_svg = get_icon_svg("trophy", size=24, color="#A3E635")

    st.markdown(
        f"""
        <div class="foodlens-xp-header" style="background: linear-gradient(135deg, #144730 0%, #1B5E3F 60%, #2E7D56 100%); border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 18px; padding: 18px 22px; color: #FFFFFF !important; margin-bottom: 22px; box-shadow: 0 10px 25px -5px rgba(27, 94, 63, 0.35), inset 0 1px 1px rgba(255, 255, 255, 0.2);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="width: 44px; height: 44px; border-radius: 12px; background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.25); display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(0,0,0,0.15);">
                        {trophy_svg}
                    </div>
                    <div>
                        <div style="font-size: 11px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.8px; color: #A3E635 !important;">CURRENT RANK</div>
                        <div style="font-size: 19px; font-weight: 800; color: #FFFFFF !important; letter-spacing: -0.2px;">{level}</div>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.15); border-radius: 12px; padding: 7px 14px; display: flex; align-items: center; gap: 6px;" title="Active daily scan streak">
                        {flame_svg}
                        <b style="font-size: 15px; color: #FFFFFF !important;">{current_streak}</b>
                        <span style="font-size: 11px; color: rgba(255,255,255,0.85) !important;">day streak</span>
                    </div>
                    <div style="background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.15); border-radius: 12px; padding: 7px 14px; display: flex; align-items: center; gap: 6px;" title="{streak_freezes} streak freeze shield(s) protecting you">
                        {shield_svg}
                        <b style="font-size: 15px; color: #FFFFFF !important;">{streak_freezes}</b>
                        <span style="font-size: 11px; color: rgba(255,255,255,0.85) !important;">freeze</span>
                    </div>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 12.5px; margin-bottom: 8px; color: rgba(255,255,255,0.95) !important;">
                <span style="color: #FFFFFF !important;"><b style="color: #A3E635 !important; font-size: 14px;">{xp} XP</b> Earned</span>
                <span style="color: rgba(255,255,255,0.85) !important;">{next_xp} XP for Next Rank</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.progress(progress_ratio)
