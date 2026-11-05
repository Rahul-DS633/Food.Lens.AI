"""
FoodLens AI — Scan & Correction Screen
State machine: Capture -> Review / Edit -> Result
"""

import streamlit as st
from pathlib import Path
from db.session import SessionLocal
from db.models import Product, Nutrition, UserProgress, XPEvent
from foodlens.barcode import decode_barcode_from_image, clean_barcode, validate_ean13
from foodlens.off_client import OpenFoodFactsClient
from foodlens.ocr import OCREngine
from foodlens.parser import parse_ocr_text
from foodlens.validation import validate_nutrition_profile
from foodlens.scoring import calculate_foodlens_score
from foodlens.ingredients import IngredientEngine
from foodlens.nutrition import Nutrient, NutritionProfile, create_nutrient
from foodlens.gamification.xp import calculate_xp_award

st.set_page_config(page_title="Scan Food — FoodLens AI", page_icon="📸", layout="wide")

CSS_PATH = Path(__file__).parent.parent / "assets" / "theme.css"
if CSS_PATH.exists():
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# State Machine Initialization
if "scan_step" not in st.session_state:
    st.session_state.scan_step = "capture"  # capture -> review -> result
if "extracted_profile_dict" not in st.session_state:
    st.session_state.extracted_profile_dict = {}
if "low_confidence_fields" not in st.session_state:
    st.session_state.low_confidence_fields = []
if "temp_product_meta" not in st.session_state:
    st.session_state.temp_product_meta = {}

off_client = OpenFoodFactsClient()
ingredient_engine = IngredientEngine()
ocr_engine = OCREngine()

st.title("📸 FoodLens Scanner")

# ----------------- STEP 1: CAPTURE -----------------
if st.session_state.scan_step == "capture":
    st.markdown(
        """
        Point your camera at the **barcode** or the **nutrition facts panel**.<br>
        If the barcode is known, your product opens instantly. If unknown or unlisted, our OCR extracts every field for your verification.
        """,
        unsafe_allow_html=True
    )

    tab1, tab2, tab3 = st.tabs(["📷 Camera Scan", "📁 Upload Photo", "⌨️ Manual Barcode / Text"])

    uploaded_bytes = None

    with tab1:
        camera_img = st.camera_input("Capture product barcode or nutrition table")
        if camera_img:
            uploaded_bytes = camera_img.getvalue()

    with tab2:
        file_img = st.file_uploader("Upload product packaging photo", type=["jpg", "jpeg", "png", "webp"])
        if file_img:
            uploaded_bytes = file_img.getvalue()

    with tab3:
        st.markdown("#### Direct Barcode Lookup")
        barcode_input = st.text_input("Enter 13-digit EAN Barcode (e.g., 8901719101052)")
        if st.button("Search Barcode", type="primary"):
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
                            # Save to DB
                            new_prod = Product(
                                barcode=clean_code,
                                name=info["name"],
                                brand=info["brand"],
                                category=info.get("category", "general"),
                                net_weight_g=info.get("net_weight_g"),
                                serving_size_g=info.get("serving_size_g"),
                                source="api",
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
                            db.commit()
                            st.session_state.current_scan_product_id = new_prod.id
                            st.switch_page("pages/2_Result.py")
                        else:
                            st.warning("Barcode not found in Open Food Facts. Please upload a photo of the nutrition label below for OCR extraction.")
                finally:
                    db.close()

        st.markdown("---")
        st.markdown("#### Paste Nutrition Facts Text")
        pasted_text = st.text_area("Paste label text (e.g. Energy 450 kcal, Protein 7g, Sugars 24g)", height=120)
        if st.button("Parse Label Text"):
            if pasted_text:
                lines = [l.strip() for l in pasted_text.splitlines() if l.strip()]
                parsed_prof, details = parse_ocr_text(lines)
                st.session_state.extracted_profile_dict = parsed_prof.to_dict()
                st.session_state.low_confidence_fields = details["low_confidence_fields"]
                st.session_state.temp_product_meta = {
                    "name": "Custom Scanned Food",
                    "brand": "Label Extraction",
                    "category": "general",
                    "serving_size_g": parsed_prof.serving_size_g,
                    "net_weight_g": 100.0,
                    "ingredients_text": "",
                }
                st.session_state.scan_step = "review"
                st.rerun()

    # If an image was taken or uploaded
    if uploaded_bytes:
        with st.spinner("Analyzing image for barcodes and nutrition facts..."):
            # 1. Try Barcode
            decoded_barcode, _ = decode_barcode_from_image(uploaded_bytes)
            if decoded_barcode:
                clean_b = clean_barcode(decoded_barcode)
                db = SessionLocal()
                try:
                    existing = db.query(Product).filter(Product.barcode == clean_b).first()
                    if existing:
                        st.success(f"Recognized Barcode: {clean_b} ({existing.name})")
                        st.session_state.current_scan_product_id = existing.id
                        st.switch_page("pages/2_Result.py")
                finally:
                    db.close()

            # 2. Run OCR Pipeline
            ocr_lines = ocr_engine.extract_text_from_image(uploaded_bytes)
            if ocr_lines:
                lines = [l.text for l in ocr_lines]
                confs = [l.confidence for l in ocr_lines]
                parsed_prof, details = parse_ocr_text(lines, confs)

                st.session_state.extracted_profile_dict = parsed_prof.to_dict()
                st.session_state.low_confidence_fields = details["low_confidence_fields"]
                st.session_state.temp_product_meta = {
                    "name": "Scanned Product",
                    "brand": "Package OCR",
                    "category": "drinks" if parsed_prof.is_beverage else "general",
                    "serving_size_g": parsed_prof.serving_size_g,
                    "net_weight_g": 100.0,
                    "ingredients_text": "\n".join(lines),
                }
                st.session_state.scan_step = "review"
                st.rerun()
            else:
                st.error("No readable barcode or text detected. Please ensure clear lighting and text orientation.")


# ----------------- STEP 2: REVIEW & CORRECTION -----------------
elif st.session_state.scan_step == "review":
    st.subheader("🔍 Review & Correct Extracted Values")
    st.markdown(
        """
        Verify the numbers read by OCR. Low-confidence fields are highlighted in amber.
        **You will earn +15 XP for verifying and confirming this record!**
        """
    )

    prof_data = st.session_state.extracted_profile_dict
    nutrients = prof_data.get("nutrients", {})
    low_confs = set(st.session_state.low_confidence_fields)

    def _get_val(k: str):
        item = nutrients.get(k)
        if isinstance(item, dict):
            return item.get("value")
        return item

    col_meta1, col_meta2 = st.columns(2)
    with col_meta1:
        p_name = st.text_input("Product Name", value=st.session_state.temp_product_meta.get("name", "Product"))
        brand = st.text_input("Brand", value=st.session_state.temp_product_meta.get("brand", ""))
        category = st.selectbox("Category", ["general", "snacks", "biscuits", "beverages", "cereals", "spreads"])
    with col_meta2:
        net_wt = st.number_input("Net Weight (g/ml)", value=float(st.session_state.temp_product_meta.get("net_weight_g", 100.0)), step=5.0)
        serve_sz = st.number_input("Serving Size (g/ml)", value=float(st.session_state.temp_product_meta.get("serving_size_g") or 25.0), step=1.0)
        basis = st.selectbox("Label Basis", ["per_100g", "per_100ml", "per_serving"])

    st.markdown("#### Nutritional Values")
    col_n1, col_n2, col_n3 = st.columns(3)

    with col_n1:
        energy_val = st.number_input(
            f"⚡ Energy (kcal) {'⚠️ Check' if 'energy_kcal' in low_confs else ''}",
            value=float(_get_val("energy_kcal") or 0.0), step=1.0
        )
        prot_val = st.number_input(
            f"💪 Protein (g) {'⚠️ Check' if 'protein_g' in low_confs else ''}",
            value=float(_get_val("protein_g") or 0.0), step=0.1
        )
        carb_val = st.number_input(
            f"🌾 Carbohydrates (g) {'⚠️ Check' if 'carbs_g' in low_confs else ''}",
            value=float(_get_val("carbs_g") or 0.0), step=0.5
        )

    with col_n2:
        sug_val = st.number_input(
            f"🍭 Total Sugars (g) {'⚠️ Check' if 'sugars_g' in low_confs else ''}",
            value=float(_get_val("sugars_g") or 0.0), step=0.5
        )
        addsug_val = st.number_input(
            f"🍯 Added Sugars (g) {'⚠️ Check' if 'added_sugar_g' in low_confs else ''}",
            value=float(_get_val("added_sugar_g") or 0.0), step=0.5
        )
        fibre_val = st.number_input(
            f"🥦 Dietary Fibre (g) {'⚠️ Check' if 'fibre_g' in low_confs else ''}",
            value=float(_get_val("fibre_g") or 0.0), step=0.1
        )

    with col_n3:
        fat_val = st.number_input(
            f"🥑 Total Fat (g) {'⚠️ Check' if 'fat_g' in low_confs else ''}",
            value=float(_get_val("fat_g") or 0.0), step=0.5
        )
        sf_val = st.number_input(
            f"🧈 Saturated Fat (g) {'⚠️ Check' if 'sat_fat_g' in low_confs else ''}",
            value=float(_get_val("sat_fat_g") or 0.0), step=0.1
        )
        sod_val = st.number_input(
            f"🧂 Sodium (mg) {'⚠️ Check' if 'sodium_mg' in low_confs else ''}",
            value=float(_get_val("sodium_mg") or 0.0), step=10.0
        )

    ing_text = st.text_area("Ingredients Statement", value=st.session_state.temp_product_meta.get("ingredients_text", ""))

    c_btn1, c_btn2 = st.columns([2, 1])
    with c_btn1:
        if st.button("✓ Looks Right — Confirm & Save (+15 XP)", type="primary", use_container_width=True):
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
                    new_p = Product(
                        barcode=f"OCR-{int(st.session_state.user_id)}-{int(st.session_state.get('timestamp', 12345))}",
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

                    # Award XP
                    progress = db.query(UserProgress).filter(UserProgress.user_id == st.session_state.user_id).first()
                    if progress:
                        xp_gain = calculate_xp_award("correction")
                        progress.xp += xp_gain
                        db.add(XPEvent(user_id=st.session_state.user_id, event_type="correction", xp=xp_gain, ref_id=str(new_p.id)))

                    db.commit()
                    st.session_state.current_scan_product_id = new_p.id
                    st.session_state.scan_step = "capture"
                    st.switch_page("pages/2_Result.py")
                finally:
                    db.close()

    with c_btn2:
        if st.button("Cancel / Rescan"):
            st.session_state.scan_step = "capture"
            st.rerun()
