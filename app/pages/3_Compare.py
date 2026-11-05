"""
FoodLens AI — Product Comparison
Side-by-side per-100g nutritional evaluation to highlight sugar, fat, and sodium differences.
"""

import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Compare Foods — FoodLens AI", page_icon="⚖️", layout="wide")

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

ingredient_engine = IngredientEngine()

st.title("⚖️ Side-by-Side Product Comparison")
st.markdown("Compare 2 or more packaged products per **100g** to spot hidden sugars, saturated fat, and sodium differences.")

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

    st.markdown("---")

    # Comparison Columns
    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.markdown(
            f"""
            <div class="foodlens-card" style="border-top: 5px solid #1B5E3F;">
                <h3 style="margin-top: 0; color: #1B5E3F;">{p1.name}</h3>
                <div style="font-size: 14px; color: #4B5563;"><b>{p1.brand}</b> • {p1.category.title()}</div>
                <div style="margin: 12px 0;">
                    <span style="font-size: 28px; font-weight: 800; color: {sc1.color_hex};">{sc1.score or 'N/A'}/100</span>
                    <span style="font-size: 14px; font-weight: 600; color: #4B5563;">({sc1.band})</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_c2:
        st.markdown(
            f"""
            <div class="foodlens-card" style="border-top: 5px solid #2563EB;">
                <h3 style="margin-top: 0; color: #2563EB;">{p2.name}</h3>
                <div style="font-size: 14px; color: #4B5563;"><b>{p2.brand}</b> • {p2.category.title()}</div>
                <div style="margin: 12px 0;">
                    <span style="font-size: 28px; font-weight: 800; color: {sc2.color_hex};">{sc2.score or 'N/A'}/100</span>
                    <span style="font-size: 14px; font-weight: 600; color: #4B5563;">({sc2.band})</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Detailed Table of Nutrients per 100g
    st.subheader("📊 Nutrient Table (Normalized Per 100g)")

    def _diff_text(v1, v2, unit, lower_is_better=True):
        if v1 is None or v2 is None:
            return "—"
        diff = round(v1 - v2, 1)
        if abs(diff) < 0.1:
            return "Identical"
        if (diff < 0 and lower_is_better) or (diff > 0 and not lower_is_better):
            return f"🟢 {p1.brand} has {abs(diff):g}{unit} {'less' if diff < 0 else 'more'}"
        else:
            return f"🔴 {p1.brand} has {abs(diff):g}{unit} {'more' if diff > 0 else 'less'}"

    metrics = [
        ("Energy", n1.energy_kcal, n2.energy_kcal, "kcal", True),
        ("Total Sugars", n1.sugars_g, n2.sugars_g, "g", True),
        ("Added Sugars", n1.added_sugar_g, n2.added_sugar_g, "g", True),
        ("Sugar in Teaspoons", prof1.sugar_teaspoons, prof2.sugar_teaspoons, " tsp", True),
        ("Total Fat", n1.fat_g, n2.fat_g, "g", True),
        ("Saturated Fat", n1.sat_fat_g, n2.sat_fat_g, "g", True),
        ("Protein", n1.protein_g, n2.protein_g, "g", False),  # Higher is better
        ("Dietary Fibre", n1.fibre_g, n2.fibre_g, "g", False), # Higher is better
        ("Sodium", n1.sodium_mg, n2.sodium_mg, "mg", True),
    ]

    import pandas as pd
    rows = []
    for m_label, v1, v2, unit, lower_is_better in metrics:
        v1_str = f"{v1:g} {unit}" if v1 is not None else "Not reported"
        v2_str = f"{v2:g} {unit}" if v2 is not None else "Not reported"
        comparison = _diff_text(v1, v2, unit, lower_is_better)
        rows.append({
            "Nutrient": m_label,
            f"{p1.brand} ({p1.name[:15]}...)": v1_str,
            f"{p2.brand} ({p2.name[:15]}...)": v2_str,
            "Key Difference": comparison
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

finally:
    db.close()
