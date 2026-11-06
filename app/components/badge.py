"""
FoodLens AI — Achievement Badge Component
Renders an achievement badge with vector medal/trophy iconography,
metallic badge gradients, and 3D tactile elevation.
"""

import streamlit as st
from typing import Dict, Any
from app.components.icons import get_icon_svg

_BADGE_ICON_MAP = {
    "FIRST_SCAN": "camera",
    "BARCODE_HUNTER": "barcode",
    "SHARP_EYES": "eye",
    "SUGAR_SPOTTER": "cubes",
    "SERVING_SIZE_SLEUTH": "scale",
    "COMPARISON_CHAMPION": "scale",
    "HINDI_EXPLORER": "award",
    "PROFILE_SET_UP": "shield",
}


def render_badge_card(badge: Dict[str, Any]):
    """
    Renders an achievement badge tile with vector icon and 3D card depth.
    """
    unlocked = badge.get("unlocked", False)
    code = badge.get("code", "")
    title = badge.get("title", "Achievement")
    desc = badge.get("description", "")

    icon_key = _BADGE_ICON_MAP.get(code, "award")
    badge_color = "#166534" if unlocked else "#94A3B8"
    icon_svg = get_icon_svg(icon_key, size=28, color=badge_color)

    bg = "linear-gradient(180deg, #FFFFFF 0%, #F0FDF4 100%)" if unlocked else "#F8FAFC"
    border = "#86EFAC" if unlocked else "#E2E8F0"
    opacity = "1.0" if unlocked else "0.6"
    shadow = "0 8px 18px rgba(27, 94, 63, 0.12)" if unlocked else "0 2px 4px rgba(0,0,0,0.02)"

    st.markdown(
        f"""
        <div class="badge-card-3d" style="background: {bg}; border: 1.5px solid {border}; border-radius: 16px; padding: 18px 14px; text-align: center; opacity: {opacity}; box-shadow: {shadow}; height: 100%; transition: all 0.2s ease;">
            <div style="width: 54px; height: 54px; margin: 0 auto 10px auto; border-radius: 50%; background: {'#DCFCE7' if unlocked else '#F1F5F9'}; display: flex; align-items: center; justify-content: center; box-shadow: inset 0 2px 4px rgba(0,0,0,0.06);">
                {icon_svg}
            </div>
            <div style="font-weight: 800; font-size: 14.5px; color: #0F172A; margin-bottom: 5px;">{title}</div>
            <div style="font-size: 12px; color: #64748B; line-height: 1.4; min-height: 34px;">{desc}</div>
            <div style="margin-top: 10px;">
                <span style="font-size: 11px; font-weight: 800; letter-spacing: 0.5px; padding: 3px 10px; border-radius: 20px; background: {'#DCFCE7' if unlocked else '#E2E8F0'}; color: {'#166534' if unlocked else '#64748B'};">
                    {'✓ UNLOCKED' if unlocked else 'LOCKED'}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
