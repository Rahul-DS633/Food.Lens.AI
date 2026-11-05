"""
FoodLens AI — Result Screen & Live Portion Calculator
"""

import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Product Analysis — FoodLens AI", page_icon="🥗", layout="wide")

CSS_PATH = Path(__file__).parent.parent / "assets" / "theme.css"
if CSS_PATH.exists():
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from db.session import SessionLocal
from db.models import Product, Nutrition
from foodlens.nutrition import (
    NutritionProfile, create_nutrient, calculate_portion, scale_profile
)
from foodlens.scoring import calculate_foodlens_score
from foodlens.validation import validate_nutrition_profile
from foodlens.ingredients import IngredientEngine
from foodlens.advisor import AIAdvisor
from app.components.nutrient_card import render_nutrient_card
from app.components.score_ring import render_score_ring
from app.components.sugar_cubes import render_sugar_cubes

ingredient_engine = IngredientEngine()
advisor = AIAdvisor()

# Get product ID from session state or query param
product_id = st.session_state.get("current_scan_product_id")
if not product_id:
    # Default to first product if none selected
    product_id = 1

db = SessionLocal()
try:
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        st.error("Product not found. Please scan or select a product first.")
        if st.button("Go to Scanner"):
            st.switch_page("pages/1_Scan.py")
        st.stop()

    n = prod.nutrition
    if not n:
        st.error("No nutrition facts recorded for this product.")
        st.stop()

    # Build reference 100g profile
    base_profile = NutritionProfile(
        basis="per_100g",
        energy_kcal=create_nutrient(n.energy_kcal, "kcal", basis="per_100g", source=prod.source),
        protein_g=create_nutrient(n.protein_g, "g", basis="per_100g", source=prod.source),
        carbs_g=create_nutrient(n.carbs_g, "g", basis="per_100g", source=prod.source),
        sugars_g=create_nutrient(n.sugars_g, "g", basis="per_100g", source=prod.source),
        added_sugar_g=create_nutrient(n.added_sugar_g, "g", basis="per_100g", source=prod.source),
        fat_g=create_nutrient(n.fat_g, "g", basis="per_100g", source=prod.source),
        sat_fat_g=create_nutrient(n.sat_fat_g, "g", basis="per_100g", source=prod.source),
        trans_fat_g=create_nutrient(n.trans_fat_g, "g", basis="per_100g", source=prod.source),
        fibre_g=create_nutrient(n.fibre_g, "g", basis="per_100g", source=prod.source),
        sodium_mg=create_nutrient(n.sodium_mg, "mg", basis="per_100g", source=prod.source),
        serving_size_g=prod.serving_size_g or 25.0,
        net_weight_g=prod.net_weight_g or 100.0,
        is_beverage=(prod.category in ("beverages", "drinks"))
    )

    score_res = calculate_foodlens_score(base_profile, category=prod.category)
    val_res = validate_nutrition_profile(base_profile)

    # Top Header & Metadata
    grade_class = f"pill-grade-{prod.quality_grade.lower()}" if prod.quality_grade else "pill-grade-b"
    source_label = prod.source.upper() if prod.source else "OFF"

    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 4px;">
                <span class="pill-badge {grade_class}">Data Grade {prod.quality_grade or 'B'}</span>
                <span class="pill-badge pill-source">Source: {source_label}</span>
                <span class="pill-badge pill-source">Status: {prod.verification_status.title()}</span>
            </div>
            <h1 style="margin: 0; color: #1B5E3F;">{prod.name}</h1>
            <div style="font-size: 16px; color: #4B5563; margin-bottom: 12px;"><b>Brand:</b> {prod.brand or 'Packaged Brand'} • <b>Category:</b> {prod.category.title()} • <b>Barcode:</b> <code>{prod.barcode}</code></div>
            """,
            unsafe_allow_html=True
        )
    with col_h2:
        if st.button("← Scan Another", use_container_width=True):
            st.switch_page("pages/1_Scan.py")
        if st.button("⚖️ Compare", use_container_width=True):
            st.switch_page("pages/3_Compare.py")

    st.markdown("---")

    # Portion Selector & Multiplier (§9.4 & §12.3)
    st.subheader("🍽️ Portion Calculator (Live Recalculation)")
    portion_options = ["Standard (100g / 100ml)"]
    if prod.serving_size_g:
        portion_options.append(f"1 Serving ({prod.serving_size_g:g}g)")
    if prod.net_weight_g:
        servings_cnt = round(prod.net_weight_g / (prod.serving_size_g or 25.0), 1)
        portion_options.append(f"Whole Packet ({prod.net_weight_g:g}g • ~{servings_cnt} serves)")
    portion_options.append("Custom Grams")

    selected_portion = st.radio(
        "Select Portion Basis",
        portion_options,
        horizontal=True,
        label_visibility="collapsed"
    )

    custom_grams = None
    if selected_portion == "Standard (100g / 100ml)":
        active_profile = base_profile
        portion_label = "per 100g"
    elif "1 Serving" in selected_portion:
        active_profile = calculate_portion(base_profile, "serving", servings=1.0)
        portion_label = f"1 serving ({prod.serving_size_g:g}g)"
    elif "Whole Packet" in selected_portion:
        active_profile = calculate_portion(base_profile, "packet")
        portion_label = f"the whole packet ({prod.net_weight_g:g}g)"
    else:
        custom_grams = st.slider("Enter consumed grams", min_value=5.0, max_value=500.0, value=50.0, step=5.0)
        active_profile = calculate_portion(base_profile, "custom", custom_grams=custom_grams)
        portion_label = f"{custom_grams:g} grams"

    # Main Grid: Left = Nutrition Facts & Sugar Cubes, Right = Score & Grounds
    col_main, col_side = st.columns([2, 1])

    with col_main:
        st.markdown(f"#### Nutrition for {portion_label.title()}")

        c1, c2, c3 = st.columns(3)
        with c1:
            render_nutrient_card(
                "Calories",
                active_profile.energy_kcal.value if active_profile.energy_kcal else None,
                "kcal",
                daily_ref_limit=2000.0,
                source=prod.source
            )
            render_nutrient_card(
                "Carbohydrates",
                active_profile.carbs_g.value if active_profile.carbs_g else None,
                "g",
                daily_ref_limit=260.0,
                source=prod.source
            )
            render_nutrient_card(
                "Dietary Fibre",
                active_profile.fibre_g.value if active_profile.fibre_g else None,
                "g",
                daily_ref_limit=28.0,
                source=prod.source
            )

        with c2:
            render_nutrient_card(
                "Total Sugars",
                active_profile.sugars_g.value if active_profile.sugars_g else None,
                "g",
                daily_ref_limit=50.0,
                source=prod.source,
                is_attention=(active_profile.sugars_g and active_profile.sugars_g.value and active_profile.sugars_g.value > 15.0)
            )
            render_nutrient_card(
                "Added Sugars",
                active_profile.added_sugar_g.value if active_profile.added_sugar_g else None,
                "g",
                daily_ref_limit=25.0,
                source=prod.source
            )
            render_nutrient_card(
                "Protein",
                active_profile.protein_g.value if active_profile.protein_g else None,
                "g",
                daily_ref_limit=50.0,
                source=prod.source
            )

        with c3:
            render_nutrient_card(
                "Total Fat",
                active_profile.fat_g.value if active_profile.fat_g else None,
                "g",
                daily_ref_limit=70.0,
                source=prod.source
            )
            render_nutrient_card(
                "Saturated Fat",
                active_profile.sat_fat_g.value if active_profile.sat_fat_g else None,
                "g",
                daily_ref_limit=20.0,
                source=prod.source,
                is_attention=(active_profile.sat_fat_g and active_profile.sat_fat_g.value and active_profile.sat_fat_g.value > 6.0)
            )
            render_nutrient_card(
                "Sodium",
                active_profile.sodium_mg.value if active_profile.sodium_mg else None,
                "mg",
                daily_ref_limit=2000.0,
                source=prod.source,
                is_attention=(active_profile.sodium_mg and active_profile.sodium_mg.value and active_profile.sodium_mg.value > 500.0)
            )

        # Sugar in Teaspoons Visualizer
        sug_val = active_profile.sugars_g.value if active_profile.sugars_g else None
        render_sugar_cubes(sug_val, portion_label=portion_label)

    with col_side:
        st.markdown("#### Category Score (v1.0)")
        render_score_ring(score_res.score, score_res.band, score_res.color_hex, version=score_res.scoring_version)

        with st.expander("Score Reasons & Breakdown", expanded=True):
            for r in score_res.reasons:
                st.markdown(f"• {r}")
            st.caption(score_res.disclaimer)

        # Ingredients & Allergen Banner
        ing_text = ", ".join([i.name for i in prod.ingredients]) if prod.ingredients else ""
        ing_res = ingredient_engine.analyze(ing_text)

        st.markdown("#### Allergen Notice")
        if ing_res.has_allergens:
            st.error(f"⚠️ {ing_res.allergen_banner}")
        else:
            st.info(f"ℹ️ {ing_res.allergen_banner}")

    st.markdown("---")

    # Grounded AI Advisor Section (§9.7)
    st.subheader("🤖 Grounded AI Advisor")
    st.caption("Deterministic numbers verified; language model explains context without medical speculation.")

    payload = advisor.build_input_payload(
        product_name=prod.name,
        brand=prod.brand,
        category=prod.category,
        profile=active_profile,
        score_res=score_res,
        ing_res=ing_res,
        portion_basis=portion_label
    )

    explanation = advisor.generate_explanation(payload)

    col_adv1, col_adv2 = st.columns([3, 2])
    with col_adv1:
        st.markdown(
            f"""
            <div class="foodlens-card">
                <h4 style="color: #1B5E3F; margin-top: 0;">Summary</h4>
                <p>{explanation.summary}</p>
                <h4 style="color: #1B5E3F;">Portion Guidance</h4>
                <p>{explanation.portion_guidance}</p>
                <h4 style="color: #1B5E3F;">Macronutrient Analysis</h4>
                <p>• {explanation.protein}</p>
                <p>• {explanation.sugar}</p>
                <p>• {explanation.fat}</p>
                <p>• {explanation.sodium}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_adv2:
        with st.expander("🛡️ Evidence Panel & Grounding Post-Check", expanded=True):
            st.markdown(f"**Groundedness Status:** {'✅ Verified (100% Numbers Match Input)' if explanation.is_grounded else '⚠️ Flagged'}")
            st.markdown(f"**Citations:** Every number matches verified label values:")
            st.json(explanation.evidence_numbers_used)
            st.caption("Refusal rule active: No medical diagnosis or disease causation claims.")

finally:
    db.close()
