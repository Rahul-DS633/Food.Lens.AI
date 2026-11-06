"""
FoodLens AI — Result Screen & Live Portion Calculator
Features realistic product packaging photography, vector iconography,
3D isometric sugar cubes visualizer, and grounded AI explanations.
"""

import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st

st.set_page_config(page_title="Product Analysis — FoodLens AI", page_icon="🔍", layout="wide")

CSS_PATH = Path(__file__).parent.parent / "assets" / "theme.css"
if CSS_PATH.exists():
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from db.session import SessionLocal
from db.models import Product, Nutrition, Ingredient, UserProfile
from foodlens.nutrition import (
    NutritionProfile, create_nutrient, calculate_portion, scale_profile
)
from foodlens.scoring import calculate_foodlens_score
from foodlens.validation import validate_nutrition_profile
from foodlens.ingredients import IngredientEngine
from foodlens.allergens import AllergenEngine, AllergenStatus
from foodlens.personal_fit import PersonalFitEngine, UserProfileData, PersonalFitVerdict
from foodlens.advisor import AIAdvisor
from app.components.nutrient_card import render_nutrient_card
from app.components.score_ring import render_score_ring
from app.components.sugar_cubes import render_sugar_cubes
from app.components.icons import get_icon_svg, icon_badge
from app.components.images import get_product_image

ingredient_engine = IngredientEngine()
allergen_engine = AllergenEngine()
personal_fit_engine = PersonalFitEngine()
advisor = AIAdvisor()

if "user_id" not in st.session_state:
    st.session_state.user_id = 1
if "language" not in st.session_state:
    st.session_state.language = "en"

# Get product ID from session state or default
product_id = st.session_state.get("current_scan_product_id") or 1

db = SessionLocal()
try:
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        st.error("Product record not found. Please scan or select a product first.")
        if st.button("Go to Scanner", width="stretch"):
            st.switch_page("pages/1_Scan.py")
        st.stop()

    n = prod.nutrition
    if not n:
        st.error("No nutritional values recorded for this product.")
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

    # Resolve User Profile for Personal Food Fit
    user_prof = st.session_state.get("user_profile")
    if not user_prof:
        db_p = db.query(UserProfile).filter(UserProfile.user_id == st.session_state.user_id).first()
        if db_p:
            user_prof = {
                "name": db_p.name,
                "age": db_p.age,
                "weight_kg": db_p.weight_kg,
                "allergies": db_p.allergies_json or [],
                "custom_allergens": db_p.custom_allergens_text or "",
                "consent_given": db_p.consent_given,
                "parental_consent_given": db_p.parental_consent_given,
            }
            st.session_state.user_profile = user_prof

    ing_text = ", ".join([ing.name for ing in prod.ingredients]) if prod.ingredients else ""

    # Top Allergen Banner (Red / Amber / Neutral)
    if user_prof and (user_prof.get("allergies") or user_prof.get("custom_allergens")):
        custom_algs = [c.strip() for c in user_prof.get("custom_allergens", "").split(",") if c.strip()]
        allergen_res = allergen_engine.check_allergens(
            ingredients_text=ing_text,
            user_allergies=user_prof.get("allergies", []),
            custom_allergens=custom_algs,
        )

        if allergen_res.overall_status == AllergenStatus.CONTAINS_YOUR_ALLERGEN:
            st.markdown(
                f"""
                <div style="background: #FEE2E2; border: 2px solid #EF4444; border-radius: 14px; padding: 14px 18px; margin-bottom: 18px; display: flex; align-items: center; gap: 14px; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.15);">
                    <div style="width: 38px; height: 38px; border-radius: 50%; background: #DC2626; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: white; font-size: 22px; font-weight: bold;">
                        !
                    </div>
                    <div>
                        <div style="color: #991B1B; font-weight: 800; font-size: 15px; margin-bottom: 2px;">
                            {allergen_res.banner_text}
                        </div>
                        <div style="color: #B91C1C; font-size: 12.5px;">
                            Matches your declared allergies ({', '.join(user_prof.get('allergies', []))}). Please inspect the package before consuming.
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        elif allergen_res.overall_status == AllergenStatus.MAY_CONTAIN_TRACES:
            st.markdown(
                f"""
                <div style="background: #FEF3C7; border: 2px solid #F59E0B; border-radius: 14px; padding: 14px 18px; margin-bottom: 18px; display: flex; align-items: center; gap: 14px; box-shadow: 0 4px 12px rgba(245, 158, 11, 0.12);">
                    <div style="width: 38px; height: 38px; border-radius: 50%; background: #D97706; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: white; font-size: 20px;">
                        ⚠️
                    </div>
                    <div>
                        <div style="color: #92400E; font-weight: 800; font-size: 15px; margin-bottom: 2px;">
                            {allergen_res.banner_text}
                        </div>
                        <div style="color: #B45309; font-size: 12.5px;">
                            Precautionary statement detected on packaging. Facility cross-contact is possible.
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        elif allergen_res.overall_status == AllergenStatus.UNKNOWN:
            st.markdown(
                f"""
                <div style="background: #FEF3C7; border: 1.5px solid #F59E0B; border-radius: 12px; padding: 12px 16px; margin-bottom: 16px; color: #92400E; font-size: 13.5px;">
                    {allergen_res.banner_text}
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div style="background: #F0FDF4; border: 1.5px solid #86EFAC; border-radius: 12px; padding: 10px 16px; margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between;">
                    <div style="color: #166534; font-size: 13.5px; font-weight: 600;">
                        ✓ None of your selected allergens ({', '.join(user_prof.get('allergies', []))}) detected in readable text. Verify on the pack.
                    </div>
                    <span style="font-size: 12px; color: #166534; font-weight: 700;">Allergen Shield Active</span>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.markdown(
            """
            <div style="background: #F8FAFC; border: 1.5px dashed #CBD5E1; border-radius: 12px; padding: 10px 16px; margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between;">
                <div style="color: #475569; font-size: 13px;">
                    🛡️ <b>Want personalized allergen alerts & portion guidance?</b> Configure your dietary profile.
                </div>
                <span style="font-size: 12.5px; color: #1B5E3F; font-weight: 700;">Use Profile Page in Menu</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Top Hero Showcase with Realistic Packaging Photo
    img_uri = get_product_image(prod.name, prod.brand, prod.category, prod.image_url)
    grade_class = f"pill-grade-{prod.quality_grade.lower()}" if prod.quality_grade else "pill-grade-b"
    source_label = prod.source.upper() if prod.source else "OFF"

    check_icon = get_icon_svg("check_circle", size=14, color="#166534")
    barcode_icon = get_icon_svg("barcode", size=16, color="#475569")
    scale_icon = get_icon_svg("scale", size=16, color="#1B5E3F")
    cam_icon = get_icon_svg("camera", size=16, color="#1B5E3F")

    col_h_img, col_h_info, col_h_acts = st.columns([1.2, 2.8, 1.2])

    with col_h_img:
        st.markdown(
            f"""
            <div style="width: 100%; height: 175px; border-radius: 16px; overflow: hidden; background: #FFFFFF; border: 1.5px solid #E2E8F0; box-shadow: 0 10px 20px -5px rgba(0,0,0,0.06); display: flex; align-items: center; justify-content: center;">
                <img src="{img_uri}" alt="{prod.name}" style="width: 100%; height: 100%; object-fit: cover;">
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_h_info:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                <span class="pill-badge {grade_class}">{check_icon} Data Grade {prod.quality_grade or 'B'}</span>
                <span class="pill-badge pill-source">Source: {source_label}</span>
                <span class="pill-badge pill-source">Status: {prod.verification_status.title()}</span>
            </div>
            <h1 style="margin: 0 0 6px 0; color: #144730; font-size: 28px;">{prod.name}</h1>
            <div style="font-size: 14.5px; color: #475569; line-height: 1.5;">
                <b>Brand:</b> <span style="color: #0F172A; font-weight: 700;">{prod.brand or 'Packaged Brand'}</span> • 
                <b>Category:</b> <span style="text-transform: capitalize;">{prod.category}</span> • 
                <b>Net Wt:</b> {prod.net_weight_g or 100:g}g • 
                <b>Serving:</b> {prod.serving_size_g or 25:g}g
            </div>
            <div style="margin-top: 6px; font-size: 13px; color: #64748B; display: flex; align-items: center; gap: 6px;">
                {barcode_icon} <code>{prod.barcode}</code>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_h_acts:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if st.button("← Scan Another", width="stretch"):
            st.switch_page("pages/1_Scan.py")
        if st.button("⚖️ Compare Product", width="stretch", type="primary"):
            st.switch_page("pages/3_Compare.py")

    st.markdown("<hr style='border: none; border-top: 1.5px solid #E2E8F0; margin: 18px 0;'>", unsafe_allow_html=True)

    # Portion Selector & Multiplier
    utensils_icon = get_icon_svg("utensils", size=20, color="#1B5E3F")
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            {utensils_icon}
            <h3 style="margin: 0; color: #144730; font-size: 18px;">Live Portion Calculator</h3>
        </div>
        """,
        unsafe_allow_html=True
    )

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
    active_portion_grams = 100.0
    if selected_portion == "Standard (100g / 100ml)":
        active_profile = base_profile
        portion_label = "per 100g"
        active_portion_grams = 100.0
    elif "1 Serving" in selected_portion:
        active_profile = calculate_portion(base_profile, "serving", servings=1.0)
        portion_label = f"1 serving ({prod.serving_size_g:g}g)"
        active_portion_grams = float(prod.serving_size_g or 25.0)
    elif "Whole Packet" in selected_portion:
        active_profile = calculate_portion(base_profile, "packet")
        portion_label = f"the whole packet ({prod.net_weight_g:g}g)"
        active_portion_grams = float(prod.net_weight_g or 100.0)
    else:
        custom_grams = st.slider("Enter consumed grams", min_value=5.0, max_value=500.0, value=50.0, step=5.0)
        active_profile = calculate_portion(base_profile, "custom", custom_grams=custom_grams)
        portion_label = f"{custom_grams:g} grams"
        active_portion_grams = float(custom_grams)

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

        # 3D Sugar Cubes Visualizer
        sug_val = active_profile.sugars_g.value if active_profile.sugars_g else None
        render_sugar_cubes(sug_val, portion_label=portion_label)

    with col_side:
        st.markdown("#### Category Score (v1.0)")
        render_score_ring(score_res.score, score_res.band, score_res.color_hex, version=score_res.scoring_version)

        with st.expander("Score Reasons & Breakdown", expanded=True):
            for r in score_res.reasons:
                st.markdown(f"• {r}")
            st.caption(score_res.disclaimer)

        # Ingredients & Allergen Notice
        ing_text = ", ".join([i.name for i in prod.ingredients]) if prod.ingredients else ""
        ing_res = ingredient_engine.analyze(ing_text)

        st.markdown("#### Allergen Notice")
        if ing_res.has_allergens:
            st.error(f"⚠️ {ing_res.allergen_banner}")
        else:
            st.info(f"ℹ️ {ing_res.allergen_banner}")

    # ═════════════════ INGREDIENTS & RECIPE COMPONENTS ═════════════════
    st.markdown("<hr style='border: none; border-top: 1.5px solid #E2E8F0; margin: 24px 0;'>", unsafe_allow_html=True)
    leaf_icon = get_icon_svg("leaf", size=22, color="#166534")
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
            {leaf_icon}
            <h2 style="margin: 0; color: #144730; font-size: 20px;">What's Inside — Ingredient & Recipe Components</h2>
        </div>
        <p style="color: #64748B; font-size: 13.5px; margin-bottom: 14px;">
            Packaged food ingredients are listed in descending order of weight. Here is what this product is made of:
        </p>
        """,
        unsafe_allow_html=True
    )

    if prod.ingredients:
        categories = {}
        for ing in prod.ingredients:
            cat = ing.category or "ingredient"
            categories[cat] = categories.get(cat, 0) + 1

        stat_chips = " • ".join([f"<b>{count}</b> {cat.replace('_', ' ').title()}" for cat, count in categories.items()])
        st.markdown(
            f"""
            <div style="background: #F0FDF4; border: 1.5px solid #86EFAC; border-radius: 12px; padding: 12px 16px; margin-bottom: 16px; font-size: 14px; color: #166534; box-shadow: 0 2px 6px rgba(0,0,0,0.02);">
                <b>{len(prod.ingredients)} Components Identified:</b> {stat_chips}
            </div>
            """,
            unsafe_allow_html=True
        )

        ing_cols = st.columns(2)
        for idx, ing in enumerate(prod.ingredients):
            with ing_cols[idx % 2]:
                allergen_badge = (
                    f"<span style='background: #FEE2E2; color: #991B1B; font-size: 10px; font-weight: 800; padding: 2px 6px; border-radius: 4px; margin-left: 6px;'>ALLERGEN: {ing.allergen_flag.upper()}</span>"
                    if (ing.allergen_flag and ing.allergen_flag != "none") else ""
                )
                cat_name = (ing.category or 'ingredient').replace('_', ' ').upper()
                st.markdown(
                    f"""
                    <div class="foodlens-card-3d" style="padding: 12px 16px; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <span style="font-size: 14.5px; font-weight: 800; color: #144730;">
                                #{ing.position} {ing.name}
                            </span>
                            <span style="font-size: 10.5px; font-weight: 800; padding: 3px 8px; border-radius: 6px; background: #ECFCCB; color: #365314; letter-spacing: 0.3px;">
                                {cat_name}
                            </span>
                        </div>
                        {allergen_badge}
                        <div style="font-size: 12.5px; color: #475569; margin-top: 4px; line-height: 1.4;">
                            {ing.explanation or 'Standard approved food-grade component.'}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.info("No structured ingredients recorded yet for this product.")
        with st.expander("➕ Add / Paste Ingredients to Analyze"):
            pasted_ing = st.text_area("Paste ingredients statement (e.g. Potatoes, Palmolein Oil, Besan, Salt, Spices)", height=80)
            if st.button("Save & Analyze Ingredients", type="primary", width="stretch"):
                if pasted_ing.strip():
                    analyzed = ingredient_engine.analyze(pasted_ing.strip())
                    for item in analyzed.ingredients:
                        db.add(Ingredient(
                            product_id=prod.id,
                            position=item.position,
                            name=item.cleaned_name,
                            category=item.category,
                            explanation=item.explanation,
                            allergen_flag=item.allergen_tag or "none"
                        ))
                    db.commit()
                    st.rerun()

    # Personal Food Fit & Grounded AI Section
    st.markdown("<hr style='border: none; border-top: 1.5px solid #E2E8F0; margin: 24px 0;'>", unsafe_allow_html=True)
    sparkles_icon = get_icon_svg("sparkles", size=22, color="#1B5E3F")
    shield_icon = get_icon_svg("shield", size=22, color="#1B5E3F")

    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
            {shield_icon}
            <h2 style="margin: 0; color: #144730; font-size: 20px;">Personalized Food Fit & Grounded AI Advice</h2>
        </div>
        <p style="color: #64748B; font-size: 13.5px; margin-bottom: 14px;">
            Evaluated relative to your dietary profile and standard ICMR-NIN & FSSAI daily reference intakes.
        </p>
        """,
        unsafe_allow_html=True
    )

    # 1. Compute deterministic personal fit
    user_obj = None
    if user_prof:
        custom_algs = [c.strip() for c in user_prof.get("custom_allergens", "").split(",") if c.strip()]
        user_obj = UserProfileData(
            name=user_prof.get("name", "User"),
            age=int(user_prof.get("age", 25)),
            weight_kg=user_prof.get("weight_kg"),
            allergies=user_prof.get("allergies", []),
            custom_allergens=custom_algs,
            consent_given=user_prof.get("consent_given", True),
            parental_consent_given=user_prof.get("parental_consent_given", False),
        )
    else:
        user_obj = UserProfileData(name="Guest", age=25, allergies=[])

    fit_result = personal_fit_engine.calculate_fit(
        profile=base_profile,
        user=user_obj,
        portion_grams=active_portion_grams,
        ingredients_text=ing_text,
    )

    # 2. Build Advisor explanation (user name strictly omitted)
    advisor_fit_payload = advisor.build_personal_fit_payload(
        fit=fit_result,
        product_name=prod.name,
        category=prod.category or "general",
        user_name=user_obj.name,
        user_age=user_obj.age,
        user_weight_kg=user_obj.weight_kg,
    )
    fit_explanation = advisor.generate_personal_fit_explanation(advisor_fit_payload)

    # Verdict badge styling
    verdict_style_map = {
        PersonalFitVerdict.FITS_WELL: ("#DCFCE7", "#166534", "✓"),
        PersonalFitVerdict.FITS_IN_MODERATION: ("#DBEAFE", "#1E40AF", "⚖️"),
        PersonalFitVerdict.BETTER_OCCASIONALLY: ("#FEF3C7", "#92400E", "⏳"),
        PersonalFitVerdict.ALLERGEN_ALERT: ("#FEE2E2", "#991B1B", "🚨"),
        PersonalFitVerdict.NOT_ENOUGH_DATA: ("#F1F5F9", "#475569", "ℹ️"),
    }
    bg_v, col_v, icon_v = verdict_style_map.get(fit_result.verdict, ("#F1F5F9", "#475569", "•"))

    col_fit_main, col_fit_side = st.columns([3, 2])

    with col_fit_main:
        st.markdown(
            f"""
            <div class="foodlens-card-3d" style="margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid #E2E8F0; padding-bottom: 10px;">
                    <div>
                        <span style="font-size: 13px; color: #64748B; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">Personal Fit Verdict</span>
                        <div style="font-size: 19px; font-weight: 900; color: #144730;">For a {active_portion_grams:g}g portion</div>
                    </div>
                    <span style="background: {bg_v}; color: {col_v}; padding: 6px 14px; border-radius: 20px; font-weight: 800; font-size: 14px;">
                        {icon_v} {fit_result.verdict.value}
                    </span>
                </div>
                <div style="font-size: 14px; color: #334155; line-height: 1.5; margin-bottom: 14px;">
                    {fit_explanation.summary}
                </div>
                <h4 style="color: #144730; margin: 12px 0 6px 0; font-size: 14px;">Portion Tip</h4>
                <p style="font-size: 13px; color: #475569; margin: 0 0 12px 0;">{fit_explanation.portion_tip}</p>
                <h4 style="color: #144730; margin: 12px 0 6px 0; font-size: 14px;">Generic Category Alternatives to Look For</h4>
                <ul style="font-size: 13px; color: #475569; margin: 0 0 12px 0; padding-left: 20px;">
                    {''.join([f'<li>{alt}</li>' for alt in fit_explanation.alternatives_to_look_for])}
                </ul>
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 12px; font-size: 11.5px; color: #64748B; margin-top: 14px;">
                    <b>Disclaimer:</b> {fit_result.disclaimer}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_fit_side:
        st.markdown(
            """
            <div class="foodlens-card-3d" style="margin-bottom: 14px;">
                <h4 style="color: #144730; margin-top: 0; font-size: 15px;">Daily Reference Contribution</h4>
                <p style="font-size: 12px; color: #64748B; margin-bottom: 10px;">
                    Based on standard ICMR-NIN & FSSAI RDA guidelines for this portion.
                </p>
            """,
            unsafe_allow_html=True
        )

        for flag in fit_result.nutrient_flags:
            bar_color = "#16A34A" if flag.severity == "green" else ("#F59E0B" if flag.severity == "amber" else "#DC2626")
            pct_capped = min(100.0, flag.pct_of_reference)
            st.markdown(
                f"""
                <div style="margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; font-size: 12.5px; font-weight: 700; color: #334155; margin-bottom: 2px;">
                        <span>{flag.display_name}</span>
                        <span>{flag.portion_value} {flag.unit} ({flag.pct_of_reference}%)</span>
                    </div>
                    <div style="width: 100%; height: 7px; background: #E2E8F0; border-radius: 4px; overflow: hidden;">
                        <div style="width: {pct_capped}%; height: 100%; background: {bar_color}; border-radius: 4px;"></div>
                    </div>
                    <div style="font-size: 11px; color: #64748B; margin-top: 2px;">{flag.reason}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        if fit_result.missing_data:
            st.caption(f"Unstated on label: {', '.join(fit_result.missing_data)}")

        with st.expander("🛡️ Evidence Panel & Grounding Post-Check", expanded=False):
            st.markdown(f"**Groundedness:** {'✅ 100% Numbers Match Input' if fit_explanation.is_grounded else '⚠️ Flagged'}")
            st.markdown(f"**Verified Evidence Numbers:**")
            st.json(fit_explanation.evidence_numbers_used)
            st.caption("Refusal rule active: No medical diagnosis, no weight goals, no commercial brand promotion.")

        st.markdown("</div>", unsafe_allow_html=True)

finally:
    db.close()
