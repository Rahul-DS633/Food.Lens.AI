"""
FoodLens AI — Scan & Correction Screen
State machine: Capture -> Review / Edit -> Result
Supports multi-photo packaging uploads, camera capture batches,
OCR extraction, deterministic review, and ingredient decomposition.
"""

import sys
import time
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st
from db.session import SessionLocal
from db.models import Product, Nutrition, Ingredient, Scan, UserProgress, XPEvent
from foodlens.barcode import decode_barcode_from_image, clean_barcode, validate_ean13
from foodlens.off_client import OpenFoodFactsClient
from foodlens.ocr import OCREngine
from foodlens.parser import parse_ocr_text, extract_ingredients_from_lines, extract_product_and_brand
from foodlens.validation import validate_nutrition_profile
from foodlens.scoring import calculate_foodlens_score
from foodlens.ingredients import IngredientEngine
from foodlens.nutrition import Nutrient, NutritionProfile, create_nutrient
from foodlens.gamification.xp import calculate_xp_award

from app.components.icons import get_icon_svg, icon_badge

st.set_page_config(page_title="Scan Food — FoodLens AI", page_icon="🔍", layout="wide")

CSS_PATH = Path(__file__).parent.parent / "assets" / "theme.css"
if CSS_PATH.exists():
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Safe Session State Initialization ──
if "user_id" not in st.session_state:
    st.session_state.user_id = 1
if "language" not in st.session_state:
    st.session_state.language = "en"
if "current_scan_product_id" not in st.session_state:
    st.session_state.current_scan_product_id = None
if "scan_step" not in st.session_state:
    st.session_state.scan_step = "capture"  # capture -> review -> result
if "extracted_profile_dict" not in st.session_state:
    st.session_state.extracted_profile_dict = {}
if "low_confidence_fields" not in st.session_state:
    st.session_state.low_confidence_fields = []
if "temp_product_meta" not in st.session_state:
    st.session_state.temp_product_meta = {}
if "camera_batch_images" not in st.session_state:
    st.session_state.camera_batch_images = []

off_client = OpenFoodFactsClient()
ingredient_engine = IngredientEngine()
ocr_engine = OCREngine()

cam_svg = get_icon_svg("camera", size=28, color="#144730")
st.markdown(
    f"""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
        {cam_svg}
        <h1 style="margin: 0; color: #144730; font-size: 28px;">FoodLens Multi-Angle Scanner</h1>
    </div>
    """,
    unsafe_allow_html=True
)


def process_images_batch(image_bytes_list):
    """
    Processes a list of image bytes (e.g. front photo, nutrition table, ingredients panel).
    1. Checks for barcode in ANY photo.
    2. Runs OCR across ALL photos and aggregates text lines in sequence.
    3. Extracts nutrition values and ingredient statements.
    """
    if not image_bytes_list:
        st.warning("Please upload or capture at least one photo first.")
        return

    progress_bar = st.progress(0.0)
    status_text = st.empty()

    # Step 1: Barcode Scan across all images
    status_text.text("🔍 Scanning images for barcodes...")
    progress_bar.progress(0.2)

    detected_barcode = None
    for img_bytes in image_bytes_list:
        code, _ = decode_barcode_from_image(img_bytes)
        if code:
            detected_barcode = clean_barcode(code)
            break

    if detected_barcode:
        status_text.text(f"✅ Barcode recognized: {detected_barcode}. Looking up product...")
        progress_bar.progress(0.5)

        db = SessionLocal()
        try:
            existing = db.query(Product).filter(Product.barcode == detected_barcode).first()
            if existing:
                st.session_state.current_scan_product_id = existing.id
                progress_bar.progress(1.0)
                st.success(f"Recognized Product: {existing.name} ({existing.brand})")
                st.switch_page("pages/2_Result.py")
                return

            # Check Open Food Facts
            info, off_prof = off_client.fetch_product(detected_barcode)
            if info and off_prof:
                new_prod = Product(
                    barcode=detected_barcode,
                    name=info["name"],
                    brand=info["brand"],
                    category=info.get("category", "general"),
                    net_weight_g=info.get("net_weight_g"),
                    serving_size_g=info.get("serving_size_g"),
                    source="api",
                    verification_status="verified",
                    quality_grade="A"
                )
                db.add(new_prod)
                db.flush()

                nutr = info.get("nutrients", {})
                db.add(Nutrition(
                    product_id=new_prod.id,
                    energy_kcal=nutr.get("energy_kcal"),
                    protein_g=nutr.get("protein_g"),
                    carbs_g=nutr.get("carbs_g"),
                    sugars_g=nutr.get("sugars_g"),
                    added_sugar_g=nutr.get("added_sugar_g"),
                    fat_g=nutr.get("fat_g"),
                    sat_fat_g=nutr.get("sat_fat_g"),
                    trans_fat_g=nutr.get("trans_fat_g"),
                    fibre_g=nutr.get("fibre_g"),
                    sodium_mg=nutr.get("sodium_mg"),
                ))

                # Save ingredients if provided
                ing_text = info.get("ingredients_text", "")
                if ing_text:
                    ing_analysis = ingredient_engine.analyze(ing_text)
                    for ing in ing_analysis.ingredients:
                        db.add(Ingredient(
                            product_id=new_prod.id,
                            position=ing.position,
                            name=ing.cleaned_name,
                            category=ing.category,
                            explanation=ing.explanation,
                            allergen_flag=ing.allergen_tag or "none"
                        ))

                db.commit()
                st.session_state.current_scan_product_id = new_prod.id
                progress_bar.progress(1.0)
                st.success(f"Fetched from Open Food Facts: {new_prod.name}")
                st.switch_page("pages/2_Result.py")
                return
        finally:
            db.close()

    # Step 2: Multi-Image OCR
    status_text.text(f"📸 Running OCR on {len(image_bytes_list)} photo(s)...")
    all_lines = []
    all_confs = []

    for idx, img_bytes in enumerate(image_bytes_list):
        step_progress = 0.3 + (0.5 * (idx + 1) / len(image_bytes_list))
        progress_bar.progress(step_progress)
        status_text.text(f"Extracting text from photo {idx + 1} of {len(image_bytes_list)}...")

        ocr_lines = ocr_engine.extract_text_from_image(img_bytes)
        for l in ocr_lines:
            all_lines.append(l.text)
            all_confs.append(l.confidence)

    progress_bar.progress(0.9)
    status_text.text("Parsing nutritional facts & ingredients...")

    if all_lines:
        parsed_prof, details = parse_ocr_text(all_lines, all_confs)
        detected_ingredients = extract_ingredients_from_lines(all_lines)

        st.session_state.extracted_profile_dict = parsed_prof.to_dict()
        st.session_state.low_confidence_fields = details["low_confidence_fields"]

        # Intelligently detect brand, product name, and category
        guessed_name, guessed_brand, guessed_cat = extract_product_and_brand(all_lines)
        detected_serve_sz = details.get("serving_size_g") or 20.0
        detected_net_wt = details.get("detected_net_weight_g") or 100.0

        st.session_state.temp_product_meta = {
            "name": guessed_name,
            "brand": guessed_brand,
            "category": guessed_cat,
            "serving_size_g": detected_serve_sz,
            "net_weight_g": detected_net_wt,
            "ingredients_text": detected_ingredients if detected_ingredients else "",
        }
        progress_bar.progress(1.0)
        status_text.empty()
        st.session_state.scan_step = "review"
        st.rerun()
    else:
        progress_bar.empty()
        status_text.empty()
        st.error("No readable barcode or text detected in the uploaded photo(s). Please ensure good lighting and clear text.")


# ═════════════════ STEP 1: CAPTURE / UPLOAD ═════════════════
if st.session_state.scan_step == "capture":
    st.markdown(
        """
        <div class="foodlens-card" style="border-left: 4px solid #1B5E3F;">
            <b style="color: #1B5E3F;">Multi-Photo Packaging Scanner:</b><br>
            You can capture or upload <b>multiple photos</b> of a product (e.g. <b>Photo 1:</b> Front & Barcode, <b>Photo 2:</b> Nutrition Facts Table, <b>Photo 3:</b> Ingredients List).<br>
            Our OCR engine merges them together to extract the complete nutrition and ingredient breakdown!
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_upload, tab_camera, tab_manual = st.tabs([
        "Upload Packaging Photos (Multiple)",
        "Live Camera (Multi-Shot)",
        "Direct Barcode Lookup"
    ])

    # ── TAB 1: UPLOAD PHOTOS FROM DEVICE ──
    with tab_upload:
        st.markdown("#### Upload One or More Packaging Photos")
        st.caption("Select photos from your computer, phone, or gallery (hold Ctrl or Shift to select multiple images).")

        uploaded_files = st.file_uploader(
            "Choose packaging photos",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
            key="multi_file_uploader"
        )

        if uploaded_files:
            st.success(f"{len(uploaded_files)} file(s) selected.")

            # Show thumbnails
            thumb_cols = st.columns(min(len(uploaded_files), 4))
            for i, uf in enumerate(uploaded_files):
                with thumb_cols[i % 4]:
                    st.image(uf, caption=f"Photo {i + 1}: {uf.name[:18]}", width="stretch")

            if st.button(f"Analyze {len(uploaded_files)} Photo(s) with OCR", type="primary", key="btn_proc_upload", width="stretch"):
                image_bytes_list = [f.getvalue() for f in uploaded_files]
                process_images_batch(image_bytes_list)

    # ── TAB 2: LIVE CAMERA SCAN (MULTI-SHOT BATCH) ──
    with tab_camera:
        st.markdown("#### Take Photos with Camera")
        st.caption("Point your camera at the front label, nutrition table, or ingredients. Add multiple shots to build a full scan.")

        camera_shot = st.camera_input("Capture camera frame", key="camera_scanner_input")

        if camera_shot:
            shot_bytes = camera_shot.getvalue()
            # Avoid adding exact duplicate
            if not any(shot_bytes == b for b in st.session_state.camera_batch_images):
                st.session_state.camera_batch_images.append(shot_bytes)
                st.toast(f"Photo {len(st.session_state.camera_batch_images)} added to scan queue!")

        if st.session_state.camera_batch_images:
            st.markdown(f"**Photos in Current Batch: {len(st.session_state.camera_batch_images)}**")
            cam_cols = st.columns(min(len(st.session_state.camera_batch_images), 4))
            for i, b_data in enumerate(st.session_state.camera_batch_images):
                with cam_cols[i % 4]:
                    st.image(b_data, caption=f"Shot {i + 1}", width="stretch")

            col_c1, col_c2 = st.columns([2, 1])
            with col_c1:
                if st.button("Process All Camera Photos", type="primary", key="btn_proc_cam", width="stretch"):
                    process_images_batch(st.session_state.camera_batch_images)
            with col_c2:
                if st.button("Clear Batch", key="btn_clear_cam", width="stretch"):
                    st.session_state.camera_batch_images = []
                    st.rerun()

    # ── TAB 3: MANUAL BARCODE OR TEXT ──
    with tab_manual:
        st.markdown("#### Direct 13-Digit Barcode Lookup")
        barcode_input = st.text_input("Enter EAN Barcode (e.g. 8901719101052 for Parle-G, 8904063200142 for Bhujia)")
        if st.button("Search Barcode", type="primary", key="btn_search_manual_bar"):
            if barcode_input:
                clean_code = clean_barcode(barcode_input)
                db = SessionLocal()
                try:
                    prod = db.query(Product).filter(Product.barcode == clean_code).first()
                    if prod:
                        st.session_state.current_scan_product_id = prod.id
                        st.switch_page("pages/2_Result.py")
                    else:
                        info, off_prof = off_client.fetch_product(clean_code)
                        if info and off_prof:
                            new_prod = Product(
                                barcode=clean_code,
                                name=info["name"],
                                brand=info["brand"],
                                category=info.get("category", "general"),
                                net_weight_g=info.get("net_weight_g"),
                                serving_size_g=info.get("serving_size_g"),
                                source="api",
                                verification_status="verified",
                                quality_grade="A"
                            )
                            db.add(new_prod)
                            db.flush()

                            nutr = info.get("nutrients", {})
                            db.add(Nutrition(
                                product_id=new_prod.id,
                                energy_kcal=nutr.get("energy_kcal"),
                                protein_g=nutr.get("protein_g"),
                                carbs_g=nutr.get("carbs_g"),
                                sugars_g=nutr.get("sugars_g"),
                                added_sugar_g=nutr.get("added_sugar_g"),
                                fat_g=nutr.get("fat_g"),
                                sat_fat_g=nutr.get("sat_fat_g"),
                                trans_fat_g=nutr.get("trans_fat_g"),
                                fibre_g=nutr.get("fibre_g"),
                                sodium_mg=nutr.get("sodium_mg"),
                            ))

                            ing_text = info.get("ingredients_text", "")
                            if ing_text:
                                ing_analysis = ingredient_engine.analyze(ing_text)
                                for ing in ing_analysis.ingredients:
                                    db.add(Ingredient(
                                        product_id=new_prod.id,
                                        position=ing.position,
                                        name=ing.cleaned_name,
                                        category=ing.category,
                                        explanation=ing.explanation,
                                        allergen_flag=ing.allergen_tag or "none"
                                    ))

                            db.commit()
                            st.session_state.current_scan_product_id = new_prod.id
                            st.switch_page("pages/2_Result.py")
                        else:
                            st.warning("Barcode not found in Open Food Facts. Please upload packaging photos above.")
                finally:
                    db.close()

        st.markdown("---")
        st.markdown("#### Paste Nutrition Facts Text")
        pasted_text = st.text_area("Paste label text (e.g. Energy 450 kcal, Protein 7g, Sugars 24g)", height=120)
        if st.button("Parse Label Text", key="btn_parse_text"):
            if pasted_text:
                lines = [l.strip() for l in pasted_text.splitlines() if l.strip()]
                parsed_prof, details = parse_ocr_text(lines)
                detected_ing = extract_ingredients_from_lines(lines)

                st.session_state.extracted_profile_dict = parsed_prof.to_dict()
                st.session_state.low_confidence_fields = details["low_confidence_fields"]
                st.session_state.temp_product_meta = {
                    "name": "Custom Product",
                    "brand": "Label Extraction",
                    "category": "beverages" if parsed_prof.is_beverage else "general",
                    "serving_size_g": parsed_prof.serving_size_g or 25.0,
                    "net_weight_g": 100.0,
                    "ingredients_text": detected_ing,
                }
                st.session_state.scan_step = "review"
                st.rerun()


# ═════════════════ STEP 2: REVIEW & CORRECTION ═════════════════
elif st.session_state.scan_step == "review":
    search_icon = get_icon_svg("search", size=22, color="#144730")
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
            {search_icon}
            <h2 style="margin: 0; color: #144730; font-size: 22px;">Review & Correct Extracted Label Values</h2>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.caption(
        "Verify the numbers extracted by OCR against your packaging. Low-confidence fields are highlighted with alerts. "
        "Earn +15 XP for verifying and confirming this record!"
    )

    prof_data = st.session_state.extracted_profile_dict
    nutrients = prof_data.get("nutrients", {})
    low_confs = set(st.session_state.low_confidence_fields)

    def _get_val(k: str):
        item = nutrients.get(k)
        if isinstance(item, dict):
            return item.get("value")
        return item

    # ── Instant AI Nutritional Advice & Snapshot ──
    energy_c = float(_get_val("energy_kcal") or 0.0)
    fat_c = float(_get_val("fat_g") or 0.0)
    sat_fat_c = float(_get_val("sat_fat_g") or 0.0)
    sug_c = float(_get_val("sugars_g") or 0.0)
    sod_c = float(_get_val("sodium_mg") or 0.0)
    prot_c = float(_get_val("protein_g") or 0.0)
    serve_sz_val = float(st.session_state.temp_product_meta.get("serving_size_g") or 20.0)
    net_wt_val = float(st.session_state.temp_product_meta.get("net_weight_g") or 100.0)

    advice_items = []
    if energy_c > 0:
        serve_cals = round(energy_c * (serve_sz_val / 100.0))
        if energy_c >= 450:
            advice_items.append(f"<b>High Energy Density ({energy_c:g} kcal / 100g):</b> This is an energy-rich item. A single {serve_sz_val:g}g portion provides ~{serve_cals} kcal.")
        else:
            advice_items.append(f"<b>Energy Balance:</b> {energy_c:g} kcal per 100g (~{serve_cals} kcal per {serve_sz_val:g}g serve).")

    if fat_c >= 20.0:
        advice_items.append(f"<b>Fat Content ({fat_c:g}g / 100g):</b> Saturated fat is {sat_fat_c:g}g. Portioning into a serving bowl is advised to manage intake.")

    if sug_c > 0:
        if sug_c <= 5.0:
            advice_items.append(f"<b>Low Sugar ({sug_c:g}g / 100g):</b> Excellent! This savory formulation is not a source of hidden sugars.")
        elif sug_c >= 20.0:
            advice_items.append(f"<b>Elevated Sugar Alert ({sug_c:g}g / 100g):</b> Equivalent to over 5 teaspoons of sugar per 100g.")

    if sod_c >= 500:
        pct_daily = round((sod_c / 2000.0) * 100)
        serve_sod = round(sod_c * (serve_sz_val / 100.0))
        advice_items.append(f"<b>Sodium Metric ({sod_c:g} mg / 100g):</b> ~{pct_daily}% of WHO daily reference limit (2,000mg). One {serve_sz_val:g}g serve provides ~{serve_sod} mg sodium.")

    if prot_c >= 8.0:
        advice_items.append(f"<b>Protein Source ({prot_c:g}g / 100g):</b> Notable legume/flour protein content (e.g. besan/gram flour or lentils).")

    if net_wt_val > serve_sz_val * 1.5:
        servings_cnt = round(net_wt_val / serve_sz_val, 1)
        advice_items.append(f"<b>Portion Awareness:</b> This packet contains ~{servings_cnt} standard servings ({net_wt_val:g}g total). Avoid eating directly from the pouch.")

    if advice_items:
        advice_html = "".join([f"<li style='margin-bottom: 6px;'>{item}</li>" for item in advice_items])
        ai_icon = get_icon_svg("sparkles", size=18, color="#166534")
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #F0FDF4 0%, #ECFCCB 100%); border: 1.5px solid #86EFAC; border-radius: 14px; padding: 16px 20px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(27, 94, 63, 0.06);">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                    {ai_icon}
                    <b style="font-size: 15px; color: #166534; letter-spacing: 0.2px;">FoodLens AI Instant Insights & Nutritional Analysis</b>
                </div>
                <ul style="margin: 0; padding-left: 20px; font-size: 13.5px; color: #1E293B; line-height: 1.55;">
                    {advice_html}
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )

    col_meta1, col_meta2 = st.columns(2)
    with col_meta1:
        p_name = st.text_input("Product Name", value=st.session_state.temp_product_meta.get("name", "Product"))
        brand = st.text_input("Brand", value=st.session_state.temp_product_meta.get("brand", ""))
        category = st.selectbox("Category", ["general", "snacks", "biscuits", "beverages", "cereals", "spreads", "namkeen"])
    with col_meta2:
        net_wt = st.number_input("Net Weight (g/ml)", value=float(st.session_state.temp_product_meta.get("net_weight_g", 100.0)), step=5.0)
        serve_sz = st.number_input("Serving Size (g/ml)", value=float(st.session_state.temp_product_meta.get("serving_size_g") or 25.0), step=1.0)
        basis = st.selectbox("Label Basis", ["per_100g", "per_100ml", "per_serving"])

    st.markdown("#### Nutritional Values (per chosen basis)")
    col_n1, col_n2, col_n3 = st.columns(3)

    with col_n1:
        energy_val = st.number_input(
            f"Energy (kcal) {'[Low Conf]' if 'energy_kcal' in low_confs else ''}",
            value=float(_get_val("energy_kcal") or 0.0), step=1.0
        )
        prot_val = st.number_input(
            f"Protein (g) {'[Low Conf]' if 'protein_g' in low_confs else ''}",
            value=float(_get_val("protein_g") or 0.0), step=0.1
        )
        carb_val = st.number_input(
            f"Carbohydrates (g) {'[Low Conf]' if 'carbs_g' in low_confs else ''}",
            value=float(_get_val("carbs_g") or 0.0), step=0.5
        )

    with col_n2:
        sug_val = st.number_input(
            f"Total Sugars (g) {'[Low Conf]' if 'sugars_g' in low_confs else ''}",
            value=float(_get_val("sugars_g") or 0.0), step=0.5
        )
        addsug_val = st.number_input(
            f"Added Sugars (g) {'[Low Conf]' if 'added_sugar_g' in low_confs else ''}",
            value=float(_get_val("added_sugar_g") or 0.0), step=0.5
        )
        fibre_val = st.number_input(
            f"Dietary Fibre (g) {'[Low Conf]' if 'fibre_g' in low_confs else ''}",
            value=float(_get_val("fibre_g") or 0.0), step=0.1
        )

    with col_n3:
        fat_val = st.number_input(
            f"Total Fat (g) {'[Low Conf]' if 'fat_g' in low_confs else ''}",
            value=float(_get_val("fat_g") or 0.0), step=0.5
        )
        sf_val = st.number_input(
            f"Saturated Fat (g) {'[Low Conf]' if 'sat_fat_g' in low_confs else ''}",
            value=float(_get_val("sat_fat_g") or 0.0), step=0.1
        )
        sod_val = st.number_input(
            f"Sodium (mg) {'[Low Conf]' if 'sodium_mg' in low_confs else ''}",
            value=float(_get_val("sodium_mg") or 0.0), step=10.0
        )

    st.markdown("#### Ingredients Statement")
    st.caption("Comma-separated list of ingredients. Our engine decodes INS additive numbers, detects allergens, and classifies categories.")
    ing_text = st.text_area("Ingredients Text", value=st.session_state.temp_product_meta.get("ingredients_text", ""), height=100)

    # Real-time ingredient preview
    if ing_text.strip():
        preview_analysis = ingredient_engine.analyze(ing_text)
        with st.expander(f"Preview Ingredients Breakdown ({len(preview_analysis.ingredients)} components identified)", expanded=True):
            if preview_analysis.has_allergens:
                st.warning(f"Allergens: {preview_analysis.allergen_banner}")
            else:
                st.info(f"Allergen Status: {preview_analysis.allergen_banner}")

            cols = st.columns(2)
            for idx, ing in enumerate(preview_analysis.ingredients):
                with cols[idx % 2]:
                    st.markdown(
                        f"""
                        <div class="foodlens-card-3d" style="padding: 10px 14px; margin-bottom: 8px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <b style="color: #144730; font-size: 13.5px;">{ing.position}. {ing.cleaned_name}</b>
                                <span style="font-size: 10.5px; padding: 2px 7px; border-radius: 6px; background: #DCFCE7; color: #166534; font-weight: 700;">
                                    {ing.category.upper()}
                                </span>
                            </div>
                            <div style="font-size: 12px; color: #475569; margin-top: 3px;">{ing.explanation}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

    st.markdown("<hr style='border: none; border-top: 1.5px solid #E2E8F0; margin: 20px 0;'>", unsafe_allow_html=True)
    c_btn1, c_btn2 = st.columns([2, 1])
    with c_btn1:
        if st.button("Confirm & Save Verified Record (+15 XP)", type="primary", width="stretch"):
            # Deterministic Validation Check
            confirmed_profile = NutritionProfile(
                basis=basis,
                energy_kcal=create_nutrient(energy_val if energy_val > 0 else None, "kcal", basis=basis, source="user_confirmed"),
                protein_g=create_nutrient(prot_val if prot_val > 0 else None, "g", basis=basis, source="user_confirmed"),
                carbs_g=create_nutrient(carb_val if carb_val > 0 else None, "g", basis=basis, source="user_confirmed"),
                sugars_g=create_nutrient(sug_val if sug_val > 0 else None, "g", basis=basis, source="user_confirmed"),
                added_sugar_g=create_nutrient(addsug_val if addsug_val > 0 else None, "g", basis=basis, source="user_confirmed"),
                fat_g=create_nutrient(fat_val if fat_val > 0 else None, "g", basis=basis, source="user_confirmed"),
                sat_fat_g=create_nutrient(sf_val if sf_val > 0 else None, "g", basis=basis, source="user_confirmed"),
                fibre_g=create_nutrient(fibre_val if fibre_val > 0 else None, "g", basis=basis, source="user_confirmed"),
                sodium_mg=create_nutrient(sod_val if sod_val > 0 else None, "mg", basis=basis, source="user_confirmed"),
                serving_size_g=serve_sz,
                net_weight_g=net_wt,
            )

            val_res = validate_nutrition_profile(confirmed_profile)
            if not val_res.is_valid:
                st.error("Validation issues detected:")
                for iss in val_res.issues:
                    st.write(f"• **{iss.rule_name}**: {iss.message}")
            else:
                db = SessionLocal()
                try:
                    # Safe user_id lookup
                    current_user_id = int(st.session_state.get("user_id", 1))
                    unique_barcode = f"OCR-{current_user_id}-{int(time.time())}"

                    new_p = Product(
                        barcode=unique_barcode,
                        name=p_name,
                        brand=brand,
                        category=category,
                        net_weight_g=net_wt,
                        serving_size_g=serve_sz,
                        source="ocr",
                        verification_status="user_confirmed",
                        quality_grade=val_res.quality_grade
                    )
                    db.add(new_p)
                    db.flush()

                    db.add(Nutrition(
                        product_id=new_p.id,
                        basis=basis,
                        energy_kcal=energy_val if energy_val > 0 else None,
                        protein_g=prot_val if prot_val > 0 else None,
                        carbs_g=carb_val if carb_val > 0 else None,
                        sugars_g=sug_val if sug_val > 0 else None,
                        added_sugar_g=addsug_val if addsug_val > 0 else None,
                        fat_g=fat_val if fat_val > 0 else None,
                        sat_fat_g=sf_val if sf_val > 0 else None,
                        fibre_g=fibre_val if fibre_val > 0 else None,
                        sodium_mg=sod_val if sod_val > 0 else None,
                    ))

                    # Save parsed ingredients into database
                    if ing_text.strip():
                        ing_analysis = ingredient_engine.analyze(ing_text)
                        for ing in ing_analysis.ingredients:
                            db.add(Ingredient(
                                product_id=new_p.id,
                                position=ing.position,
                                name=ing.cleaned_name,
                                category=ing.category,
                                explanation=ing.explanation,
                                allergen_flag=ing.allergen_tag or "none"
                            ))

                    # Log scan history
                    score_res = calculate_foodlens_score(confirmed_profile, category=category)
                    db.add(Scan(
                        user_id=current_user_id,
                        product_id=new_p.id,
                        source_type="ocr",
                        score=score_res.score,
                    ))

                    # Award XP
                    progress = db.query(UserProgress).filter(UserProgress.user_id == current_user_id).first()
                    if progress:
                        xp_gain = calculate_xp_award("correction")
                        progress.xp += xp_gain
                        db.add(XPEvent(user_id=current_user_id, event_type="correction", xp=xp_gain, ref_id=str(new_p.id)))

                    db.commit()
                    st.session_state.current_scan_product_id = new_p.id
                    st.session_state.scan_step = "capture"
                    st.session_state.camera_batch_images = []
                    st.switch_page("pages/2_Result.py")
                finally:
                    db.close()

    with c_btn2:
        if st.button("Cancel / Rescan"):
            st.session_state.scan_step = "capture"
            st.session_state.camera_batch_images = []
            st.rerun()
