"""
Streamlit Component: Nutrient Card
Renders a metric card with value, unit, reference percentage bar, and provenance chip.
"""

import streamlit as st
from typing import Optional


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
    Renders a nutrient card. If value is None, displays 'Not declared' cleanly.
    """
    card_border = "#FCA5A5" if is_attention else "#E5E7EB"
    bg_color = "#FEF2F2" if is_attention else "#FFFFFF"

    st.markdown(
        f"""
        <div style="background-color: {bg_color}; border: 1.5px solid {card_border}; border-radius: 14px; padding: 14px 16px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-size: 13px; font-weight: 700; color: #4B5563; text-transform: uppercase;">{label}</span>
                <span style="font-size: 11px; padding: 2px 8px; border-radius: 10px; background: #F3F4F6; color: #6B7280;">
                    {source.upper()} {f'({int(confidence*100)}%)' if confidence < 1.0 else ''}
                </span>
            </div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 24px; font-weight: 800; color: #111827;">
                {f'{value:g} <span style="font-size: 15px; font-weight: 600; color: #6B7280;">{unit}</span>' if value is not None else '<span style="font-size: 15px; color: #9CA3AF; font-style: italic;">Not declared</span>'}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    if value is not None and daily_ref_limit and daily_ref_limit > 0:
        ratio = min(1.0, value / daily_ref_limit)
        bar_color = "#DC2626" if ratio > 0.6 else ("#F59E0B" if ratio > 0.3 else "#10B981")
        st.progress(ratio)
