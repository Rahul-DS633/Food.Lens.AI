"""
Streamlit Component: XP Bar & Level Tracker
Renders user rank, level progress bar, streak flame, and streak freeze indicators.
"""

import streamlit as st


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
    Renders top gamification status bar.
    """
    progress_ratio = 1.0 if next_xp <= base_xp else min(1.0, max(0.0, (xp - base_xp) / (next_xp - base_xp)))

    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #1B5E3F 0%, #2E7D56 100%); border-radius: 16px; padding: 16px 20px; color: #FFFFFF; margin-bottom: 20px; box-shadow: 0 4px 14px rgba(27, 94, 63, 0.2);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 28px;">{level_icon}</span>
                    <div>
                        <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.85;">CURRENT RANK</div>
                        <div style="font-size: 18px; font-weight: 800;">{level}</div>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 14px;">
                    <div style="background: rgba(255,255,255,0.15); border-radius: 12px; padding: 6px 12px; text-align: center;">
                        <span style="font-size: 14px;">🔥</span>
                        <b style="font-size: 14px;">{current_streak}</b>
                        <span style="font-size: 11px; opacity: 0.9;">days</span>
                    </div>
                    <div style="background: rgba(255,255,255,0.15); border-radius: 12px; padding: 6px 12px; text-align: center;" title="{streak_freezes} streak freezes protecting you">
                        <span style="font-size: 14px;">🛡️</span>
                        <b style="font-size: 14px;">{streak_freezes}</b>
                    </div>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 6px; opacity: 0.9;">
                <span><b>{xp} XP</b></span>
                <span>{next_xp} XP for next rank</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.progress(progress_ratio)
