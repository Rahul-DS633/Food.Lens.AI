"""
FoodLens AI — Nutrient Card Component
Renders a modern metric card with vector biomarker icon, JetBrains Mono value,
reference percentage bar, and data provenance chip.
"""

import streamlit as st
from typing import Optional
from app.components.icons import get_icon_svg, icon_badge


# Map nutrient label strings to vector icon keys and distinct accent colors
_NUTRIENT_VISUALS = {
    "calories": {"icon": "energy", "color": "#EA580C", "bg": "#FFF7ED"},
    "energy": {"icon": "energy", "color": "#EA580C", "bg": "#FFF7ED"},
    "carbohydrates": {"icon": "wheat", "color": "#CA8A04", "bg": "#FEFCE8"},
    "carbs": {"icon": "wheat", "color": "#CA8A04", "bg": "#FEFCE8"},
    "sugars": {"icon": "cubes", "color": "#2563EB", "bg": "#EFF6FF"},
    "total sugars": {"icon": "cubes", "color": "#2563EB", "bg": "#EFF6FF"},
    "added sugar": {"icon": "cubes", "color": "#0284C7", "bg": "#F0F9FF"},
    "protein": {"icon": "protein", "color": "#16A34A", "bg": "#F0FDF4"},
    "total fat": {"icon": "fat", "color": "#D97706", "bg": "#FFFBEB"},
    "fat": {"icon": "fat", "color": "#D97706", "bg": "#FFFBEB"},
    "saturated fat": {"icon": "sat_fat", "color": "#DC2626", "bg": "#FEF2F2"},
    "trans fat": {"icon": "alert", "color": "#991B1B", "bg": "#FEF2F2"},
    "dietary fibre": {"icon": "fibre", "color": "#059669", "bg": "#ECFDF5"},
    "fibre": {"icon": "fibre", "color": "#059669", "bg": "#ECFDF5"},
    "sodium": {"icon": "salt", "color": "#6366F1", "bg": "#EEF2FF"},
}


def render_nutrient_card(
    label: str,
    value: Optional[float],
    unit: str,
    daily_ref_limit: Optional[float] = None,
    source: str = "api",
    confidence: float = 1.0,
    is_attention: bool = False
):
    """
    Renders an elevated nutrient card with vector icon, value, unit, and reference ratio.
    """
    cfg = _NUTRIENT_VISUALS.get(label.lower().strip(), {"icon": "leaf", "color": "#1B5E3F", "bg": "#F0FDF4"})
    card_border = "#FCA5A5" if is_attention else "#E2E8F0"
    card_bg = "#FFF5F5" if is_attention else "#FFFFFF"

    icon_svg = get_icon_svg(cfg["icon"], size=16, color=cfg["color"])

    st.markdown(
        f"""
        <div class="nutrient-card-3d" style="background-color: {card_bg}; border: 1.5px solid {card_border}; border-radius: 14px; padding: 14px 16px; margin-bottom: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03); transition: transform 0.2s ease, box-shadow 0.2s ease;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 7px;">
                    <div style="width: 26px; height: 26px; border-radius: 8px; background: {cfg['bg']}; display: flex; align-items: center; justify-content: center;">
                        {icon_svg}
                    </div>
                    <span style="font-size: 12.5px; font-weight: 700; color: #374151; text-transform: uppercase; letter-spacing: 0.3px;">{label}</span>
                </div>
                <span style="font-size: 10.5px; font-weight: 600; padding: 2px 7px; border-radius: 8px; background: #F1F5F9; color: #475569; border: 1px solid #E2E8F0;">
                    {source.upper()} {f'({int(confidence*100)}%)' if confidence < 1.0 else ''}
                </span>
            </div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 24px; font-weight: 800; color: #0F172A; display: flex; align-items: baseline; gap: 4px;">
                {f'{value:g} <span style="font-size: 14px; font-weight: 600; color: #64748B;">{unit}</span>' if value is not None else '<span style="font-size: 14px; color: #94A3B8; font-style: italic;">Not declared</span>'}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    if value is not None and daily_ref_limit and daily_ref_limit > 0:
        ratio = min(1.0, value / daily_ref_limit)
        st.progress(ratio)
