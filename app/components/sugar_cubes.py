"""
Streamlit Component: Sugar Cubes Visualizer
Converts grams of sugar into visual teaspoons / sugar cubes (approx 4g each).
"""

import streamlit as st
from typing import Optional


def render_sugar_cubes(sugar_grams: Optional[float], portion_label: str = "this portion"):
    """
    Renders stacked sugar cubes for intuitive comprehension.
    1 teaspoon granulated sugar ≈ 4 grams.
    """
    if sugar_grams is None:
        st.markdown(
            """
            <div style="padding: 12px; background: #F9FAFB; border-radius: 12px; color: #6B7280; font-size: 13px;">
                🧊 Sugar quantity not reported on label.
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    tsps = round(sugar_grams / 4.0, 1)
    full_cubes = int(sugar_grams // 4)
    has_half = (sugar_grams % 4) >= 2

    cubes_html = "".join(['<span class="sugar-cube-box">🧊</span>' for _ in range(min(full_cubes, 20))])
    if has_half and full_cubes < 20:
        cubes_html += '<span class="sugar-cube-box" style="opacity:0.6">🧊</span>'

    st.markdown(
        f"""
        <div class="foodlens-card" style="border-left: 5px solid #3B82F6;">
            <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
                <span style="font-weight: 700; font-size: 14px; color: #1E3A8A;">SUGAR IN TEASPOONS</span>
                <span style="font-weight: 800; font-size: 16px; color: #2563EB;">{sugar_grams:g} g total sugar</span>
            </div>
            <div style="font-size: 18px; margin: 8px 0;">
                {cubes_html}
            </div>
            <div style="font-size: 13px; color: #4B5563; margin-top: 6px;">
                Equivalent to <b>~{tsps} teaspoons</b> of sugar in {portion_label}.
                <span style="color: #6B7280;">(WHO daily recommended limit: ~6 teaspoons / 25g)</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
