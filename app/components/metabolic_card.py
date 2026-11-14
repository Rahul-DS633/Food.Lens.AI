"""
FoodLens AI — Metabolic & Physiological Impact UI Component
Renders:
1. Sugar Spike Gauge (SSI) & Glycemic Buffering Breakdown.
2. Protein Density Badge & Protein Leverage Hypothesis Assessment.
3. Sodium Shock Bar & ICMR-NIN 2,000 mg Daily Ceiling Utilization.
4. Satiety & Weight Management Index (WMI) with Fullness Latency.
"""

import streamlit as st
from typing import Optional
from foodlens.nutrition import NutritionProfile
from foodlens.metabolic import analyze_metabolic_impact, MetabolicProfile
from app.components.icons import get_icon_svg


def render_metabolic_section(profile: NutritionProfile, serving_size_g: Optional[float] = None) -> None:
    """
    Renders the complete Metabolic Impact & Physiological Analysis section.
    """
    meta: MetabolicProfile = analyze_metabolic_impact(profile, serving_size_g=serving_size_g)

    st.markdown("<hr style='border: none; border-top: 1.5px solid #E2E8F0; margin: 26px 0 20px 0;'>", unsafe_allow_html=True)

    bolt_icon = get_icon_svg("bolt", size=22, color="#1B5E3F")
    st.markdown(
        f'<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">'
        f'{bolt_icon}'
        f'<h2 style="margin: 0; color: #144730; font-size: 20px;">Metabolic Impact & Physiological Insights</h2>'
        f'</div>'
        f'<p style="color: #64748B; font-size: 13.5px; margin-bottom: 16px;">'
        f'Scientific analysis of glycemic surge, protein leverage, cardiovascular fluid load, and weight dynamics based on <b>ICMR-NIN 2024</b> guidelines.'
        f'</p>',
        unsafe_allow_html=True
    )

    # 1. Top Summary Banner
    summary_bg = "#F0FDF4" if meta.weight_management.color_hex == "#166534" else ("#FEF3C7" if meta.weight_management.color_hex == "#F59E0B" else "#FEF2F2")
    summary_border = "#86EFAC" if meta.weight_management.color_hex == "#166534" else ("#FCD34D" if meta.weight_management.color_hex == "#F59E0B" else "#FCA5A5")
    summary_color = "#166534" if meta.weight_management.color_hex == "#166534" else ("#92400E" if meta.weight_management.color_hex == "#F59E0B" else "#991B1B")

    banner_html = (
        f'<div style="background: {summary_bg}; border: 1.5px solid {summary_border}; border-radius: 12px; padding: 12px 16px; margin-bottom: 18px; display: flex; align-items: center; gap: 10px;">'
        f'<span style="font-size: 20px;">🔬</span>'
        f'<div>'
        f'<b style="color: {summary_color}; font-size: 14px;">Physiological Summary:</b> '
        f'<span style="color: #1E293B; font-size: 13px;">{meta.summary_sentence}</span>'
        f'</div>'
        f'</div>'
    )
    st.markdown(banner_html, unsafe_allow_html=True)

    # 2. Four Metrics Grid
    c_m1, c_m2 = st.columns(2)

    # ── CARD 1: SUGAR SPIKE INDEX (SSI) ──
    with c_m1:
        ssi_res = meta.sugar_spike
        ssi_val = f"{ssi_res.sugar_spike_index:g}" if ssi_res.sugar_spike_index is not None else "N/A"
        gbf_val = f"{ssi_res.buffering_factor:g}x" if ssi_res.buffering_factor is not None else "1.0x"
        sugar_icon = get_icon_svg("sugar", size=18, color=ssi_res.color_hex)

        card1_html = (
            f'<div class="foodlens-card-3d" style="border-top: 4px solid {ssi_res.color_hex}; padding: 16px; height: 100%;">'
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
            f'<div style="display: flex; align-items: center; gap: 8px;">'
            f'{sugar_icon}'
            f'<span style="font-weight: 800; font-size: 14.5px; color: #0F172A;">Sugar Spike Index (SSI)</span>'
            f'</div>'
            f'<span style="background: {ssi_res.color_hex}15; color: {ssi_res.color_hex}; font-weight: 800; font-size: 11px; padding: 3px 8px; border-radius: 9999px; border: 1px solid {ssi_res.color_hex}40; text-transform: uppercase;">'
            f'{ssi_res.risk_band} Surge'
            f'</span>'
            f'</div>'
            f'<div style="font-size: 24px; font-weight: 900; color: {ssi_res.color_hex}; font-family: \'JetBrains Mono\', monospace; margin-bottom: 4px;">'
            f'{ssi_val} <span style="font-size: 13px; color: #64748B; font-weight: 600;">/ 100 SSI</span>'
            f'</div>'
            f'<div style="font-size: 12px; color: #475569; margin-bottom: 8px;">'
            f'Glycemic Buffer Factor: <b>{gbf_val}</b> (fibre & protein resistance)'
            f'</div>'
            f'<p style="font-size: 12.5px; color: #334155; line-height: 1.4; margin: 0;">'
            f'{ssi_res.explanation}'
            f'</p>'
            f'</div>'
        )
        st.markdown(card1_html, unsafe_allow_html=True)

    # ── CARD 2: PROTEIN LEVERAGE & DENSITY ──
    with c_m2:
        p_res = meta.protein_density
        pe_val = f"{p_res.protein_energy_pct:g}%" if p_res.protein_energy_pct is not None else "N/A"
        p_100k = f"{p_res.protein_per_100kcal:g}g" if p_res.protein_per_100kcal is not None else "N/A"
        protein_icon = get_icon_svg("protein", size=18, color=p_res.color_hex)

        card2_html = (
            f'<div class="foodlens-card-3d" style="border-top: 4px solid {p_res.color_hex}; padding: 16px; height: 100%;">'
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
            f'<div style="display: flex; align-items: center; gap: 8px;">'
            f'{protein_icon}'
            f'<span style="font-weight: 800; font-size: 14.5px; color: #0F172A;">Protein Density (P:E)</span>'
            f'</div>'
            f'<span style="background: {p_res.color_hex}15; color: {p_res.color_hex}; font-weight: 800; font-size: 11px; padding: 3px 8px; border-radius: 9999px; border: 1px solid {p_res.color_hex}40; text-transform: uppercase;">'
            f'{p_res.classification}'
            f'</span>'
            f'</div>'
            f'<div style="font-size: 24px; font-weight: 900; color: {p_res.color_hex}; font-family: \'JetBrains Mono\', monospace; margin-bottom: 4px;">'
            f'{pe_val} <span style="font-size: 13px; color: #64748B; font-weight: 600;">of Total Energy</span>'
            f'</div>'
            f'<div style="font-size: 12px; color: #475569; margin-bottom: 8px;">'
            f'Protein Yield: <b>{p_100k}</b> per 100 kcal consumed'
            f'</div>'
            f'<p style="font-size: 12.5px; color: #334155; line-height: 1.4; margin: 0;">'
            f'{p_res.satiety_impact}'
            f'</p>'
            f'</div>'
        )
        st.markdown(card2_html, unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    c_m3, c_m4 = st.columns(2)

    # ── CARD 3: SODIUM & FLUID RETENTION ──
    with c_m3:
        sod_res = meta.sodium
        sod_mg = f"{sod_res.sodium_mg:g} mg" if sod_res.sodium_mg is not None else "N/A"
        pct_limit = f"{sod_res.daily_limit_pct_per_serving:g}%" if sod_res.daily_limit_pct_per_serving is not None else "N/A"
        sod_icon = get_icon_svg("sodium", size=18, color=sod_res.color_hex)

        hfss_pill = (
            f'<span style="background: #FEE2E2; color: #991B1B; font-weight: 800; font-size: 10.5px; padding: 2px 7px; border-radius: 6px; border: 1px solid #FCA5A5;">FSSAI HFSS ALERT</span>'
            if sod_res.is_fssai_hfss_high else
            f'<span style="background: #DCFCE7; color: #166534; font-weight: 800; font-size: 10.5px; padding: 2px 7px; border-radius: 6px; border: 1px solid #86EFAC;">SAFE SODIUM</span>'
        )

        card3_html = (
            f'<div class="foodlens-card-3d" style="border-top: 4px solid {sod_res.color_hex}; padding: 16px; height: 100%;">'
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
            f'<div style="display: flex; align-items: center; gap: 8px;">'
            f'{sod_icon}'
            f'<span style="font-weight: 800; font-size: 14.5px; color: #0F172A;">Sodium & Fluid Balance</span>'
            f'</div>'
            f'{hfss_pill}'
            f'</div>'
            f'<div style="font-size: 24px; font-weight: 900; color: {sod_res.color_hex}; font-family: \'JetBrains Mono\', monospace; margin-bottom: 4px;">'
            f'{pct_limit} <span style="font-size: 13px; color: #64748B; font-weight: 600;">of Daily Limit per serving</span>'
            f'</div>'
            f'<div style="font-size: 12px; color: #475569; margin-bottom: 8px;">'
            f'Density: <b>{sod_mg}</b> per 100g (ICMR ceiling: 2,000 mg/day)'
            f'</div>'
            f'<p style="font-size: 12.5px; color: #334155; line-height: 1.4; margin: 0;">'
            f'{sod_res.explanation}'
            f'</p>'
            f'</div>'
        )
        st.markdown(card3_html, unsafe_allow_html=True)

    # ── CARD 4: WEIGHT MANAGEMENT & SATIETY INDEX (WMI) ──
    with c_m4:
        w_res = meta.weight_management
        wmi_val = f"{w_res.weight_management_index:g}" if w_res.weight_management_index is not None else "N/A"
        kcal_g = f"{w_res.energy_density_kcal_per_g:g} kcal/g" if w_res.energy_density_kcal_per_g is not None else "N/A"
        scale_icon = get_icon_svg("scale", size=18, color=w_res.color_hex)

        card4_html = (
            f'<div class="foodlens-card-3d" style="border-top: 4px solid {w_res.color_hex}; padding: 16px; height: 100%;">'
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
            f'<div style="display: flex; align-items: center; gap: 8px;">'
            f'{scale_icon}'
            f'<span style="font-weight: 800; font-size: 14.5px; color: #0F172A;">Weight Management & Satiety</span>'
            f'</div>'
            f'<span style="background: {w_res.color_hex}15; color: {w_res.color_hex}; font-weight: 800; font-size: 11px; padding: 3px 8px; border-radius: 9999px; border: 1px solid {w_res.color_hex}40; text-transform: uppercase;">'
            f'{w_res.verdict}'
            f'</span>'
            f'</div>'
            f'<div style="font-size: 24px; font-weight: 900; color: {w_res.color_hex}; font-family: \'JetBrains Mono\', monospace; margin-bottom: 4px;">'
            f'{wmi_val} <span style="font-size: 13px; color: #64748B; font-weight: 600;">/ 100 Satiety Score</span>'
            f'</div>'
            f'<div style="font-size: 12px; color: #475569; margin-bottom: 8px;">'
            f'Fullness Latency: <b style="color: {w_res.color_hex};">{w_res.hunger_latency}</b> ({kcal_g})'
            f'</div>'
            f'<p style="font-size: 12.5px; color: #334155; line-height: 1.4; margin: 0;">'
            f'{w_res.explanation}'
            f'</p>'
            f'</div>'
        )
        st.markdown(card4_html, unsafe_allow_html=True)
