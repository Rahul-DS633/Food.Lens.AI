"""
FoodLens AI — Product Comparison
Side-by-side per-100g nutritional evaluation with realistic product photography,
vector iconography, and direct difference analysis.
"""

import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Compare Foods — FoodLens AI", page_icon="🔍", layout="wide")

CSS_PATH = Path(__file__).parent.parent / "assets" / "theme.css"
if CSS_PATH.exists():
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from db.session import SessionLocal
from db.models import Product, UserProgress, XPEvent
from foodlens.nutrition import NutritionProfile, create_nutrient
from foodlens.scoring import calculate_foodlens_score
from foodlens.ingredients import IngredientEngine
from foodlens.gamification.xp import calculate_xp_award
from app.components.icons import get_icon_svg
from app.components.images import get_product_image
from app.components.report_modal import render_report_issue_dialog
from app.components.audio_player import render_audio_narration_player
from app.components.sidebar import render_sidebar

ingredient_engine = IngredientEngine()
render_sidebar("Compare")

scale_svg = get_icon_svg("scale", size=26, color="#144730")
st.markdown(
    f"""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
        {scale_svg}
        <h1 style="margin: 0; color: #144730; font-size: 26px;">Side-by-Side Product Comparison</h1>
    </div>
    """,
    unsafe_allow_html=True
)
st.caption("Compare 2 packaged products per 100g to spot hidden sugars, saturated fat, and sodium differences.")

db = SessionLocal()
try:
    products = db.query(Product).all()
    if len(products) < 2:
        st.info("At least 2 products must be in the database to compare.")
        st.stop()

    prod_names = {f"{p.brand} - {p.name} (#{p.id})": p.id for p in products}

    # Selection row
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        sel1 = st.selectbox("Select Product A", list(prod_names.keys()), index=0)
    with col_sel2:
        sel2 = st.selectbox("Select Product B", list(prod_names.keys()), index=min(1, len(prod_names) - 1))

    id1 = prod_names[sel1]
    id2 = prod_names[sel2]

    if id1 == id2:
        st.warning("Please select two distinct products to view differences.")
        st.stop()

    p1 = db.query(Product).filter(Product.id == id1).first()
    p2 = db.query(Product).filter(Product.id == id2).first()

    n1 = p1.nutrition
    n2 = p2.nutrition

    # Build profiles
    prof1 = NutritionProfile(
        basis="per_100g",
        energy_kcal=create_nutrient(n1.energy_kcal, "kcal"),
        protein_g=create_nutrient(n1.protein_g, "g"),
        carbs_g=create_nutrient(n1.carbs_g, "g"),
        sugars_g=create_nutrient(n1.sugars_g, "g"),
        added_sugar_g=create_nutrient(n1.added_sugar_g, "g"),
        fat_g=create_nutrient(n1.fat_g, "g"),
        sat_fat_g=create_nutrient(n1.sat_fat_g, "g"),
        fibre_g=create_nutrient(n1.fibre_g, "g"),
        sodium_mg=create_nutrient(n1.sodium_mg, "mg"),
    )
    prof2 = NutritionProfile(
        basis="per_100g",
        energy_kcal=create_nutrient(n2.energy_kcal, "kcal"),
        protein_g=create_nutrient(n2.protein_g, "g"),
        carbs_g=create_nutrient(n2.carbs_g, "g"),
        sugars_g=create_nutrient(n2.sugars_g, "g"),
        added_sugar_g=create_nutrient(n2.added_sugar_g, "g"),
        fat_g=create_nutrient(n2.fat_g, "g"),
        sat_fat_g=create_nutrient(n2.sat_fat_g, "g"),
        fibre_g=create_nutrient(n2.fibre_g, "g"),
        sodium_mg=create_nutrient(n2.sodium_mg, "mg"),
    )

    sc1 = calculate_foodlens_score(prof1, category=p1.category)
    sc2 = calculate_foodlens_score(prof2, category=p2.category)

    # Award XP for comparing
    progress = db.query(UserProgress).filter(UserProgress.user_id == 1).first()
    if progress:
        xp_gain = calculate_xp_award("compare")
        progress.xp += xp_gain
        db.add(XPEvent(user_id=1, event_type="compare", xp=xp_gain, ref_id=f"{id1}_vs_{id2}"))
        db.commit()

    st.markdown("<hr style='border: none; border-top: 1.5px solid #E2E8F0; margin: 18px 0;'>", unsafe_allow_html=True)

    # Side-by-side Realistic Product Showcase Cards
    img1 = get_product_image(p1.name, p1.brand, p1.category, p1.image_url)
    img2 = get_product_image(p2.name, p2.brand, p2.category, p2.image_url)

    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.markdown(
            f"""
            <div class="product-card-3d" style="border-top: 5px solid #1B5E3F; padding: 18px;">
                <div style="display: flex; gap: 14px; align-items: center; margin-bottom: 12px;">
                    <div style="width: 80px; height: 80px; border-radius: 12px; overflow: hidden; background: #F8FAFC; border: 1px solid #E2E8F0; flex-shrink: 0;">
                        <img src="{img1}" alt="{p1.name}" style="width: 100%; height: 100%; object-fit: cover;">
                    </div>
                    <div>
                        <span style="font-size: 11px; font-weight: 700; padding: 2px 7px; border-radius: 6px; background: #DCFCE7; color: #166534; text-transform: uppercase;">
                            {p1.brand}
                        </span>
                        <h3 style="margin: 4px 0 2px 0; color: #144730; font-size: 17px;">{p1.name}</h3>
                        <div style="font-size: 13px; color: #64748B;">Category: {p1.category.title()}</div>
                    </div>
                </div>
                <div style="background: #F8FAFC; border-radius: 10px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: baseline;">
                    <span style="font-size: 12.5px; font-weight: 700; color: #475569; text-transform: uppercase;">Nutri-Score</span>
                    <span style="font-size: 26px; font-weight: 800; color: {sc1.color_hex}; font-family: 'JetBrains Mono', monospace;">
                        {sc1.score or 'N/A'}<span style="font-size: 14px; color: #64748B;">/100 ({sc1.band})</span>
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_c2:
        st.markdown(
            f"""
            <div class="product-card-3d" style="border-top: 5px solid #2563EB; padding: 18px;">
                <div style="display: flex; gap: 14px; align-items: center; margin-bottom: 12px;">
                    <div style="width: 80px; height: 80px; border-radius: 12px; overflow: hidden; background: #F8FAFC; border: 1px solid #E2E8F0; flex-shrink: 0;">
                        <img src="{img2}" alt="{p2.name}" style="width: 100%; height: 100%; object-fit: cover;">
                    </div>
                    <div>
                        <span style="font-size: 11px; font-weight: 700; padding: 2px 7px; border-radius: 6px; background: #EFF6FF; color: #1D4ED8; text-transform: uppercase;">
                            {p2.brand}
                        </span>
                        <h3 style="margin: 4px 0 2px 0; color: #1E3A8A; font-size: 17px;">{p2.name}</h3>
                        <div style="font-size: 13px; color: #64748B;">Category: {p2.category.title()}</div>
                    </div>
                </div>
                <div style="background: #F8FAFC; border-radius: 10px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: baseline;">
                    <span style="font-size: 12.5px; font-weight: 700; color: #475569; text-transform: uppercase;">Nutri-Score</span>
                    <span style="font-size: 26px; font-weight: 800; color: {sc2.color_hex}; font-family: 'JetBrains Mono', monospace;">
                        {sc2.score or 'N/A'}<span style="font-size: 14px; color: #64748B;">/100 ({sc2.band})</span>
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Detailed Table of Nutrients per 100g
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    st.markdown("#### Nutritional Difference Breakdown (Per 100g)")

    def _diff_text(v1, v2, unit, lower_is_better=True):
        if v1 is None or v2 is None:
            return "—"
        diff = round(v1 - v2, 1)
        if abs(diff) < 0.1:
            return "Identical"
        if (diff < 0 and lower_is_better) or (diff > 0 and not lower_is_better):
            return f"Better: {p1.brand} has {abs(diff):g}{unit} {'less' if diff < 0 else 'more'}"
        else:
            return f"Higher: {p1.brand} has {abs(diff):g}{unit} {'more' if diff > 0 else 'less'}"

    metrics = [
        ("Energy", n1.energy_kcal, n2.energy_kcal, "kcal", True),
        ("Total Sugars", n1.sugars_g, n2.sugars_g, "g", True),
        ("Added Sugars", n1.added_sugar_g, n2.added_sugar_g, "g", True),
        ("Sugar in Teaspoons", prof1.sugar_teaspoons, prof2.sugar_teaspoons, " tsp", True),
        ("Total Fat", n1.fat_g, n2.fat_g, "g", True),
        ("Saturated Fat", n1.sat_fat_g, n2.sat_fat_g, "g", True),
        ("Protein", n1.protein_g, n2.protein_g, "g", False),
        ("Dietary Fibre", n1.fibre_g, n2.fibre_g, "g", False),
        ("Sodium", n1.sodium_mg, n2.sodium_mg, "mg", True),
    ]

    rows = []
    for m_label, v1, v2, unit, lower_is_better in metrics:
        v1_str = f"{v1:g} {unit}" if v1 is not None else "Not reported"
        v2_str = f"{v2:g} {unit}" if v2 is not None else "Not reported"
        comparison = _diff_text(v1, v2, unit, lower_is_better)
        rows.append({
            "Nutrient": m_label,
            f"{p1.brand} ({p1.name[:16]}...)": v1_str,
            f"{p2.brand} ({p2.name[:16]}...)": v2_str,
            "Evaluation": comparison
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, width="stretch", hide_index=True)

    # Ingredients Side-by-side
    st.markdown("#### Ingredients Comparison")
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        st.markdown(f"**{p1.name} Ingredients:**")
        if p1.ingredients:
            for item in p1.ingredients:
                st.markdown(f"- **{item.name}** ({item.category})")
        else:
            st.caption("No ingredients parsed yet.")

    with col_i2:
        st.markdown(f"**{p2.name} Ingredients:**")
        if p2.ingredients:
            for item in p2.ingredients:
                st.markdown(f"- **{item.name}** ({item.category})")
        else:
            st.caption("No ingredients parsed yet.")

    st.markdown("<hr style='border: none; border-top: 1.5px solid #E2E8F0; margin: 24px 0;'>", unsafe_allow_html=True)
    c_a1, c_a2 = st.columns(2)
    with c_a1:
        data_p1 = {
            "name": p1.name,
            "portion_grams": 100.0,
            "portion_basis": "per_100g",
            "energy_kcal": p1.nutrition.energy_kcal if p1.nutrition else None,
            "sugars_g": p1.nutrition.sugars_g if p1.nutrition else None,
            "sugar_teaspoons": round(p1.nutrition.sugars_g / 4.0, 1) if (p1.nutrition and p1.nutrition.sugars_g) else None,
            "protein_g": p1.nutrition.protein_g if p1.nutrition else None,
            "fat_g": p1.nutrition.fat_g if p1.nutrition else None,
            "sodium_mg": p1.nutrition.sodium_mg if p1.nutrition else None,
        }
        render_audio_narration_player(data_p1, default_lang="en", key_suffix="comp_p1")
    with c_a2:
        data_p2 = {
            "name": p2.name,
            "portion_grams": 100.0,
            "portion_basis": "per_100g",
            "energy_kcal": p2.nutrition.energy_kcal if p2.nutrition else None,
            "sugars_g": p2.nutrition.sugars_g if p2.nutrition else None,
            "sugar_teaspoons": round(p2.nutrition.sugars_g / 4.0, 1) if (p2.nutrition and p2.nutrition.sugars_g) else None,
            "protein_g": p2.nutrition.protein_g if p2.nutrition else None,
            "fat_g": p2.nutrition.fat_g if p2.nutrition else None,
            "sodium_mg": p2.nutrition.sodium_mg if p2.nutrition else None,
        }
        render_audio_narration_player(data_p2, default_lang="en", key_suffix="comp_p2")

    c_r1, c_r2 = st.columns(2)
    with c_r1:
        render_report_issue_dialog(p1.id, p1.name, key_suffix="comp_1")
    with c_r2:
        render_report_issue_dialog(p2.id, p2.name, key_suffix="comp_2")

finally:
    db.close()
