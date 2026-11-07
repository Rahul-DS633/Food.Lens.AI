"""
FoodLens AI — Sugar Timeline & Ingredient Highlighting Component
Renders an ordered visual timeline of ingredients showing where sugars,
syrups, bulking agents, and non-sugar sweeteners appear in descending weight order.
"""

import streamlit as st
from typing import List
from foodlens.sugar_detector import SugarReport
from app.components.icons import get_icon_svg


_CLASS_STYLE_MAP = {
    "sugars": {
        "bg": "#FEF3C7",
        "border": "#F59E0B",
        "color": "#92400E",
        "icon": "cubes",
        "label": "Sugar",
    },
    "syrups": {
        "bg": "#FFEDD5",
        "border": "#F97316",
        "color": "#9A3412",
        "icon": "cubes",
        "label": "Syrup",
    },
    "concentrates": {
        "bg": "#FEF9C3",
        "border": "#EAB308",
        "color": "#854D0E",
        "icon": "leaf",
        "label": "Fruit Concentrate",
    },
    "carb_fillers": {
        "bg": "#F3E8FF",
        "border": "#C084FC",
        "color": "#6B21A8",
        "icon": "wheat",
        "label": "Carb Bulking Agent",
    },
    "non_sugar_sweeteners": {
        "bg": "#CFFAFE",
        "border": "#22D3EE",
        "color": "#155E75",
        "icon": "shield",
        "label": "Non-Sugar Sweetener",
    },
    "ambiguous": {
        "bg": "#E0F2FE",
        "border": "#38BDF8",
        "color": "#0369A1",
        "icon": "sparkles",
        "label": "Ambiguous / Dairy Sugar",
    },
}


def render_sugar_timeline(report: SugarReport, portion_g: float = 100.0, raw_tokens: List[str] = None):
    """
    Renders the sugar timeline track, sugar splitting alert, and interactive glossary.
    """
    if report.status != "OK":
        return

    cubes_icon = get_icon_svg("cubes", size=22, color="#B45309")
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 8px; margin-top: 14px; margin-bottom: 6px;">
            {cubes_icon}
            <h3 style="margin: 0; color: #144730; font-size: 18px;">Hidden Sugar & Sweetener Timeline</h3>
        </div>
        <p style="color: #64748B; font-size: 13px; margin-bottom: 12px;">
            Ingredients appear in statutory descending weight order. Highlighted badges indicate caloric sugars, syrups, bulking fillers, or sweeteners.
        </p>
        """,
        unsafe_allow_html=True
    )

    # 1. Sugar Splitting Warning Banner
    if report.sugar_splitting:
        st.markdown(
            f"""
            <div style="background: #FEF3C7; border: 1.5px solid #F59E0B; border-radius: 12px; padding: 12px 16px; margin-bottom: 14px; box-shadow: 0 2px 6px rgba(245, 158, 11, 0.08);">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 20px;">⚠️</span>
                    <div>
                        <b style="color: #92400E; font-size: 14px;">Sugar Splitting Detected ({len(report.distinct_sugar_names)} Distinct Sugar Sources)</b>
                        <div style="color: #78350F; font-size: 12.5px; margin-top: 2px;">
                            The manufacturer has divided sweetness across <b>{', '.join(report.distinct_sugar_names)}</b>, which distributes sugar across multiple positions instead of a single prominent entry.
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 2. Label Conflict Notice
    if report.label_conflict and report.label_conflict_reason:
        st.markdown(
            f"""
            <div style="background: #EFF6FF; border: 1.5px solid #60A5FA; border-radius: 12px; padding: 12px 16px; margin-bottom: 14px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 20px;">⚖️</span>
                    <div>
                        <b style="color: #1E40AF; font-size: 14px;">Nutrition Table ↔ Ingredient List Notice</b>
                        <div style="color: #1E3A8A; font-size: 12.5px; margin-top: 2px;">
                            {report.label_conflict_reason}
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 3. Teaspoons Metric Card
    if report.portion_teaspoons is not None:
        basis_txt = "added sugar" if report.teaspoon_basis == "added_sugar" else "total sugars"
        st.markdown(
            f"""
            <div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 12px; padding: 12px 16px; margin-bottom: 14px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 4px 10px rgba(0,0,0,0.03);">
                <div>
                    <span style="font-size: 12px; color: #64748B; font-weight: 700; text-transform: uppercase;">Equivalent Sugar in {portion_g:g}g Portion</span>
                    <div style="font-size: 20px; font-weight: 900; color: #144730;">
                        About {report.portion_teaspoons:g} Teaspoons
                    </div>
                    <span style="font-size: 11px; color: #64748B;">Calculated as grams / 4.0, rounded to nearest 0.5 (based on {basis_txt}).</span>
                </div>
                <div style="text-align: right;">
                    <span style="background: #ECFCCB; color: #365314; font-weight: 800; font-size: 12px; padding: 4px 10px; border-radius: 12px;">
                        {len(report.distinct_sugar_names)} Sugar Sources
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 4. Timeline Chips List
    match_by_pos = {m.position: m for m in report.matches}
    raw_tokens = raw_tokens or [m.ingredient_text for m in report.matches]

    timeline_items_html = []
    for idx, token in enumerate(raw_tokens, start=1):
        m = match_by_pos.get(idx)
        if m:
            style = _CLASS_STYLE_MAP.get(m.sugar_class, _CLASS_STYLE_MAP["sugars"])
            fuzzy_badge = "<span style='font-size: 9.5px; opacity: 0.8;'> (OCR typo)</span>" if m.match_type == "fuzzy" else ""
            timeline_items_html.append(
                f"""
                <span style="display: inline-flex; align-items: center; gap: 5px; background: {style['bg']}; border: 1.5px solid {style['border']}; color: {style['color']}; padding: 4px 10px; border-radius: 10px; font-size: 12.5px; font-weight: 700; margin: 3px;">
                    <span style="background: {style['border']}; color: white; border-radius: 50%; width: 18px; height: 18px; display: inline-flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 800;">#{idx}</span>
                    <span>{token}</span>
                    <span style="font-size: 10px; opacity: 0.85; text-transform: uppercase;">[{style['label']}]</span>
                    {fuzzy_badge}
                </span>
                """
            )
        else:
            timeline_items_html.append(
                f"""
                <span style="display: inline-flex; align-items: center; gap: 4px; background: #F8FAFC; border: 1px solid #E2E8F0; color: #475569; padding: 4px 8px; border-radius: 8px; font-size: 12px; margin: 3px;">
                    <span style="color: #94A3B8; font-size: 10px; font-weight: 700;">#{idx}</span>
                    <span>{token}</span>
                </span>
                """
            )

    st.markdown(
        f"""
        <div class="foodlens-card-3d" style="padding: 14px; margin-bottom: 14px;">
            <div style="font-size: 12px; font-weight: 800; color: #144730; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.4px;">
                Ordered Ingredient Track (Descending Weight)
            </div>
            <div style="line-height: 2.2;">
                {''.join(timeline_items_html)}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 5. Expandable 'What Is This?' Glossary
    if report.matches:
        with st.expander("📖 What Are These Ingredients? (Neutral Educational Guide)", expanded=False):
            for m in report.matches:
                style = _CLASS_STYLE_MAP.get(m.sugar_class, _CLASS_STYLE_MAP["sugars"])
                st.markdown(
                    f"""
                    <div style="margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #F1F5F9;">
                        <span style="font-weight: 800; color: {style['color']}; font-size: 13.5px;">
                            #{m.position} {m.ingredient_text}
                        </span>
                        <span style="font-size: 11px; background: {style['bg']}; color: {style['color']}; padding: 2px 6px; border-radius: 4px; margin-left: 6px; font-weight: 700;">
                            {style['label']}
                        </span>
                        <div style="font-size: 12px; color: #475569; margin-top: 3px; line-height: 1.4;">
                            {m.explanation}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

