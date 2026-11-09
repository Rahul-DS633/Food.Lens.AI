"""
FoodLens AI — Claim Checker Chips & Evidence UI Component
Renders front-of-pack claim verification chips, detailed regulatory benchmarks,
neutral explanations, and the Myth Buster literacy card.
"""

import streamlit as st

from db.models import Product
from foodlens.claims import ClaimChecker, ClaimResult, ClaimStatus
from foodlens.nutrition import NutritionProfile
from app.components.icons import get_icon_svg


STATUS_STYLES = {
    ClaimStatus.SUPPORTED: {
        "bg": "#DCFCE7",
        "border": "#86EFAC",
        "text": "#166534",
        "icon": "✔",
        "label": "Supported",
    },
    ClaimStatus.PARTLY_SUPPORTED: {
        "bg": "#FEF3C7",
        "border": "#FCD34D",
        "text": "#92400E",
        "icon": "⚠",
        "label": "Partly Supported",
    },
    ClaimStatus.NOT_SUPPORTED: {
        "bg": "#FEE2E2",
        "border": "#FCA5A5",
        "text": "#991B1B",
        "icon": "ℹ",
        "label": "Not Supported",
    },
    ClaimStatus.CANNOT_VERIFY: {
        "bg": "#F1F5F9",
        "border": "#CBD5E1",
        "text": "#475569",
        "icon": "❓",
        "label": "Cannot Verify",
    },
    ClaimStatus.NOT_CHECKABLE: {
        "bg": "#EFF6FF",
        "border": "#BFDBFE",
        "text": "#1E40AF",
        "icon": "🏷",
        "label": "Marketing Buzzword",
    },
}


def render_claim_chip_html(result: ClaimResult) -> str:
    cfg = STATUS_STYLES.get(result.status, STATUS_STYLES[ClaimStatus.NOT_CHECKABLE])
    return (
        f'<div style="display: inline-flex; align-items: center; gap: 6px; background: {cfg["bg"]}; '
        f'border: 1px solid {cfg["border"]}; color: {cfg["text"]}; padding: 5px 12px; border-radius: 9999px; '
        f'font-size: 13px; font-weight: 700; margin: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">'
        f'<span>{cfg["icon"]}</span><span>{result.claim_text}</span>'
        f'<span style="font-size: 10.5px; opacity: 0.85; border-left: 1px solid {cfg["border"]}; padding-left: 6px; text-transform: uppercase;">'
        f'{cfg["label"]}</span></div>'
    )


def render_claims_section(
    product: Product,
    profile: NutritionProfile,
    ingredients_text: str,
    key_prefix: str = "result"
) -> None:
    """
    Renders the complete Claim Checker UI block with interactive chips and evidence drawer.
    """
    st.markdown("<hr style='border: none; border-top: 1.5px solid #E2E8F0; margin: 24px 0;'>", unsafe_allow_html=True)

    target_icon = get_icon_svg("search", size=22, color="#1D4ED8")
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
            {target_icon}
            <h2 style="margin: 0; color: #1E3A8A; font-size: 20px;">Front-of-Pack Claim Checker</h2>
        </div>
        <p style="color: #64748B; font-size: 13.5px; margin-bottom: 12px;">
            Marketing claims printed on front packaging compared directly with declared laboratory nutrition and statutory benchmark standards (FSSAI 2018 / Codex).
        </p>
        """,
        unsafe_allow_html=True
    )

    # 1. Suggested claims based on pack
    default_claims = []
    if profile.sugars_g and profile.sugars_g.value is not None and profile.sugars_g.value <= 0.5:
        default_claims.append("Sugar Free")
    if profile.protein_g and profile.protein_g.value is not None and profile.protein_g.value >= 10.0:
        default_claims.append("High Protein")
    if "whole wheat" in ingredients_text.lower() or "atta" in ingredients_text.lower():
        default_claims.append("100% Whole Wheat")
    if not default_claims:
        default_claims = ["No Added Sugar", "High Protein", "100% Natural"]

    selected_claims = st.multiselect(
        "Claims printed on this package (select or type your own):",
        options=[
            "Sugar Free", "Low Sugar", "No Added Sugar", "High Protein", "Source of Protein",
            "High Fibre", "Source of Fibre", "Fat Free", "Low Fat", "Low Saturated Fat",
            "Zero Trans Fat", "Low Sodium", "100% Whole Wheat", "Multigrain", "No Maida",
            "100% Natural", "Healthy", "Wholesome"
        ],
        default=default_claims,
        key=f"{key_prefix}_claims_input"
    )

    if not selected_claims:
        st.info("Select or add one or more marketing claims above to inspect verified label evidence.")
        return

    checker = ClaimChecker()
    summary = checker.check_claims(selected_claims, profile, ingredients_text=ingredients_text)

    # 2. Summary KPI Banner
    chip_htmls = "".join(render_claim_chip_html(r) for r in summary.results)
    st.markdown(
        f"""
        <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 12px; padding: 12px 14px; margin-bottom: 14px;">
            <div style="font-weight: 700; color: #1E293B; font-size: 14px; margin-bottom: 8px;">
                📊 Verification Summary: {summary.summary_sentence}
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 4px;">
                {chip_htmls}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 3. Evidence Expander
    with st.expander("🔬 View Statutory Benchmarks & Label Evidence", expanded=True):
        for idx, res in enumerate(summary.results):
            cfg = STATUS_STYLES.get(res.status, STATUS_STYLES[ClaimStatus.NOT_CHECKABLE])
            st.markdown(
                f"""
                <div style="border-left: 4px solid {cfg['border']}; padding: 6px 12px; margin-bottom: 12px; background: #FFFFFF; border-radius: 0 8px 8px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <span style="font-weight: 800; color: #0F172A; font-size: 14.5px;">{res.claim_text}</span>
                        <span style="background: {cfg['bg']}; color: {cfg['text']}; font-size: 11px; font-weight: 800; padding: 2px 8px; border-radius: 9999px;">
                            {cfg['label']}
                        </span>
                    </div>
                    <p style="color: #334155; font-size: 13.5px; margin: 4px 0 6px 0;">{res.neutral_explanation}</p>
                    <div style="font-size: 11.5px; color: #64748B;">
                        <b>Benchmark Rule:</b> {res.threshold_source or 'FSSAI Claims Regulations, 2018'}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.caption(
            "📌 *Legal Footnote: Based on the label data we have; claim rules can differ by product category.*"
        )

    # 4. Myth Buster Quest & Literacy Reward (+15 XP)
    if "myth_buster_claimed" not in st.session_state:
        st.session_state.myth_buster_claimed = False

    if not st.session_state.myth_buster_claimed:
        st.markdown(
            """
            <div style="background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); border: 1.5px solid #93C5FD; border-radius: 12px; padding: 12px 16px; margin-top: 14px; display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <div style="font-weight: 800; color: #1E40AF; font-size: 14px;">🔬 Myth Buster Quest</div>
                    <div style="color: #3B82F6; font-size: 12.5px;">Inspect packaging claims to unlock the <b>Myth Buster</b> milestone badge (+15 XP).</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Claim Myth Buster Reward (+15 XP)", key=f"{key_prefix}_myth_buster_btn"):
            st.session_state.myth_buster_claimed = True
            st.session_state.xp = st.session_state.get("xp", 0) + 15
            st.success("🎉 Claim verified! Unlocked the 'Myth Buster' badge and awarded +15 XP!")
            st.rerun()
