"""
FoodLens AI — 3D Sugar Cubes & Teaspoon Visualizer
Renders realistic 3D isometric sugar cubes with crystalline gradient lighting,
depth shadows, and direct conversion to culinary teaspoons (approx 4g each).
Replaces emoji representation with high-fidelity 3D visual graphics.
"""

import streamlit as st
from typing import Optional
from app.components.icons import get_icon_svg


def render_3d_cube_svg(size: int = 26, is_half: bool = False) -> str:
    """
    Renders an isometric 3D sugar cube with realistic crystal facets,
    specular light highlights, and depth shading.
    """
    opacity = "0.55" if is_half else "1.0"
    return f"""
    <div style="display: inline-block; width: {size}px; height: {size + 4}px; margin: 3px; vertical-align: middle; opacity: {opacity}; filter: drop-shadow(0 3px 4px rgba(59, 130, 246, 0.22));">
        <svg viewBox="0 0 32 36" width="{size}" height="{size + 4}" fill="none" xmlns="http://www.w3.org/2000/svg">
            <!-- Top Facet (Lightest Crystal Surface) -->
            <polygon points="16,2 30,10 16,18 2,10" fill="url(#cube-top-grad)" stroke="#93C5FD" stroke-width="1.2"/>
            <!-- Left Front Facet (Medium Shading) -->
            <polygon points="2,10 16,18 16,32 2,24" fill="url(#cube-left-grad)" stroke="#93C5FD" stroke-width="1.2"/>
            <!-- Right Front Facet (Deepest Shading) -->
            <polygon points="16,18 30,10 30,24 16,32" fill="url(#cube-right-grad)" stroke="#93C5FD" stroke-width="1.2"/>
            <!-- Subtle Specular Glare -->
            <circle cx="16" cy="11" r="2.5" fill="#FFFFFF" opacity="0.8"/>
            <defs>
                <linearGradient id="cube-top-grad" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stop-color="#FFFFFF"/>
                    <stop offset="100%" stop-color="#EFF6FF"/>
                </linearGradient>
                <linearGradient id="cube-left-grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#E0F2FE"/>
                    <stop offset="100%" stop-color="#BAE6FD"/>
                </linearGradient>
                <linearGradient id="cube-right-grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#BFDBFE"/>
                    <stop offset="100%" stop-color="#93C5FD"/>
                </linearGradient>
            </defs>
        </svg>
    </div>
    """


def render_sugar_cubes(sugar_grams: Optional[float], portion_label: str = "this portion"):
    """
    Renders stacked 3D isometric sugar cubes for intuitive comprehension.
    1 standard culinary teaspoon granulated sugar ≈ 4.0 grams.
    """
    if sugar_grams is None:
        info_icon = get_icon_svg("info", size=18, color="#6B7280")
        st.markdown(
            f"""
            <div style="padding: 14px 18px; background: #F9FAFB; border-radius: 12px; border: 1px solid #E5E7EB; color: #4B5563; font-size: 13.5px; display: flex; align-items: center; gap: 8px;">
                {info_icon}
                <span>Total sugar quantity is <b>not declared</b> on this manufacturer's label.</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    tsps = round(sugar_grams / 4.0, 1)
    full_cubes = int(sugar_grams // 4)
    has_half = (sugar_grams % 4) >= 1.5

    # Generate 3D isometric cubes
    cubes_html = "".join([render_3d_cube_svg(size=28, is_half=False) for _ in range(min(full_cubes, 24))])
    if has_half and full_cubes < 24:
        cubes_html += render_3d_cube_svg(size=28, is_half=True)

    cube_icon = get_icon_svg("cubes", size=18, color="#2563EB")

    st.markdown(
        f"""
        <div class="foodlens-card" style="border-left: 5px solid #3B82F6; background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid #E2E8F0; padding-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    {cube_icon}
                    <span style="font-weight: 700; font-size: 13.5px; color: #1E3A8A; letter-spacing: 0.5px; text-transform: uppercase;">Sugar Visualizer (3D Cubes)</span>
                </div>
                <span style="font-family: 'JetBrains Mono', monospace; font-weight: 800; font-size: 17px; color: #2563EB;">
                    {sugar_grams:g} g total sugar
                </span>
            </div>
            
            <div style="background: rgba(239, 246, 255, 0.6); border: 1.5px dashed #93C5FD; border-radius: 12px; padding: 12px 14px; margin: 10px 0;">
                <div style="font-size: 11px; font-weight: 700; color: #3B82F6; text-transform: uppercase; margin-bottom: 6px; letter-spacing: 0.5px;">
                    Crystalline Representation (1 cube = 4g)
                </div>
                <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 2px;">
                    {cubes_html}
                </div>
            </div>

            <div style="font-size: 13.5px; color: #334155; margin-top: 8px; line-height: 1.5;">
                Equivalent to <b style="color: #1E40AF; font-size: 15px;">~{tsps} teaspoons</b> of granulated sugar in {portion_label}.
                <div style="color: #64748B; font-size: 12px; margin-top: 4px;">
                    WHO daily recommended upper limit: ~6 teaspoons (25g) for a 2,000 kcal diet.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
