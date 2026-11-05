"""
Streamlit Component: Achievement Badge Tile
"""

import streamlit as st
from typing import Dict, Any


def render_badge_card(badge: Dict[str, Any]):
    unlocked = badge.get("unlocked", False)
    icon = badge.get("icon", "🏅")
    title = badge.get("title", "Badge")
    desc = badge.get("description", "")

    bg = "#F0FDF4" if unlocked else "#F9FAFB"
    border = "#86EFAC" if unlocked else "#E5E7EB"
    opacity = "1.0" if unlocked else "0.55"

    st.markdown(
        f"""
        <div style="background-color: {bg}; border: 1.5px solid {border}; border-radius: 14px; padding: 14px; text-align: center; opacity: {opacity}; height: 100%;">
            <div style="font-size: 32px; margin-bottom: 6px;">{icon}</div>
            <div style="font-weight: 800; font-size: 14px; color: #111827; margin-bottom: 4px;">{title}</div>
            <div style="font-size: 12px; color: #6B7280; line-height: 1.3;">{desc}</div>
            <div style="margin-top: 8px;">
                <span style="font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 8px; background: {'#DCFCE7' if unlocked else '#F3F4F6'}; color: {'#166534' if unlocked else '#9CA3AF'};">
                    {'✓ UNLOCKED' if unlocked else '🔒 LOCKED'}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
