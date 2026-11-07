"""
FoodLens UI Component: Report Wrong Data Modal / Expander
Allows users and guests to report inaccurate label data with validation and evidence uploads.
"""

from pathlib import Path
from typing import Dict, Any
import streamlit as st
from db.session import SessionLocal
from db.models import Product, DataReport
from foodlens.report_checks import validate_proposed_field
from foodlens.image_security import sanitize_and_save_evidence_image, ImageValidationError

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "uploads" / "evidence"

REPORTABLE_FIELDS = [
    ("name", "Product Name"),
    ("brand", "Brand Name"),
    ("category", "Product Category"),
    ("serving_size_g", "Serving Size (g)"),
    ("net_weight_g", "Net Weight (g)"),
    ("energy_kcal", "Energy (kcal)"),
    ("protein_g", "Protein (g)"),
    ("carbs_g", "Carbohydrates (g)"),
    ("sugars_g", "Total Sugars (g)"),
    ("added_sugar_g", "Added Sugar (g)"),
    ("fat_g", "Total Fat (g)"),
    ("sat_fat_g", "Saturated Fat (g)"),
    ("trans_fat_g", "Trans Fat (g)"),
    ("fibre_g", "Dietary Fibre (g)"),
    ("sodium_mg", "Sodium (mg)"),
    ("ingredients", "Ingredients List"),
    ("allergens", "Allergen Disclosures"),
]


def render_report_issue_dialog(product_id: int, product_name: str, key_suffix: str = ""):
    """
    Renders an expandable or dialog-style reporting form for an issue on the current product.
    """
    with st.expander(f"🚩 Report Incorrect Data for {product_name}", expanded=False):
        st.markdown(
            """
            <div style="font-size: 13.5px; color: #475569; margin-bottom: 12px;">
                Notice something wrong on this nutrition label or ingredient list? 
                Submit the correct values below. Our admin queue will review and publish verified corrections.
            </div>
            """,
            unsafe_allow_html=True
        )

        col_f, col_cur = st.columns([1.5, 1.5])
        
        db = SessionLocal()
        prod = None
        current_nutrients: Dict[str, Any] = {}
        try:
            prod = db.query(Product).filter(Product.id == product_id).first()
            if prod and prod.nutrition:
                n = prod.nutrition
                current_nutrients = {
                    "energy_kcal": n.energy_kcal,
                    "protein_g": n.protein_g,
                    "carbs_g": n.carbs_g,
                    "sugars_g": n.sugars_g,
                    "added_sugar_g": n.added_sugar_g,
                    "fat_g": n.fat_g,
                    "sat_fat_g": n.sat_fat_g,
                    "trans_fat_g": n.trans_fat_g,
                    "fibre_g": n.fibre_g,
                    "sodium_mg": n.sodium_mg,
                }
        finally:
            db.close()

        with col_f:
            field_choice = st.selectbox(
                "Field with inaccurate data",
                options=[f[0] for f in REPORTABLE_FIELDS],
                format_func=lambda x: dict(REPORTABLE_FIELDS).get(x, x),
                key=f"rep_field_{product_id}_{key_suffix}"
            )

        # Compute current value
        cur_val_display = "Not recorded"
        if prod:
            if hasattr(prod, field_choice):
                cur_val_display = str(getattr(prod, field_choice) or "Not recorded")
            elif prod.nutrition and hasattr(prod.nutrition, field_choice):
                cur_val_display = str(getattr(prod.nutrition, field_choice) or "Not recorded")

        with col_cur:
            st.markdown(
                f"""
                <div style="padding-top: 26px; font-size: 13px; color: #64748B;">
                    Current on FoodLens: <b>{cur_val_display}</b>
                </div>
                """,
                unsafe_allow_html=True
            )

        col_prop, col_img = st.columns([1.5, 1.5])
        with col_prop:
            proposed_val = st.text_input(
                "Proposed correct value",
                placeholder="e.g. 12.5 or exact corrected name",
                key=f"rep_val_{product_id}_{key_suffix}"
            )

        with col_img:
            evidence_file = st.file_uploader(
                "Optional pack photo evidence (PNG/JPEG, max 8MB)",
                type=["png", "jpg", "jpeg", "webp"],
                key=f"rep_file_{product_id}_{key_suffix}"
            )

        comment = st.text_area(
            "Comments / Source notes (max 500 characters)",
            max_chars=500,
            placeholder="e.g. As seen on new 2026 packaging revision from local store.",
            key=f"rep_comment_{product_id}_{key_suffix}"
        )

        consent = st.checkbox(
            "I confirm I am not sharing personal information (addresses, names, payment details) in this report.",
            value=True,
            key=f"rep_consent_{product_id}_{key_suffix}"
        )

        if st.button("Submit Report for Review", type="primary", key=f"rep_submit_{product_id}_{key_suffix}"):
            if not consent:
                st.error("You must agree to the privacy statement before submitting.")
                return

            if not proposed_val or not proposed_val.strip():
                st.error("Please enter a proposed correct value.")
                return

            # Run deterministic auto-check
            check = validate_proposed_field(field_choice, proposed_val.strip(), current_nutrients)
            
            # Handle image upload if provided
            saved_image_path = None
            if evidence_file:
                try:
                    file_bytes = evidence_file.read()
                    dest_dir = DATA_DIR / f"prod_{product_id}"
                    dest_path = dest_dir / f"ev_{int(st.session_state.get('user_id', 1))}_{evidence_file.name}"
                    _, ext = sanitize_and_save_evidence_image(file_bytes, evidence_file.name, dest_path)
                    saved_image_path = str(dest_path.as_posix())
                except ImageValidationError as e:
                    st.error(f"Image error: {e}")
                    return

            # Save report
            db = SessionLocal()
            try:
                rep = DataReport(
                    product_id=product_id,
                    field=field_choice,
                    current_value=cur_val_display,
                    proposed_value=proposed_val.strip(),
                    evidence_image_path=saved_image_path,
                    comment=comment.strip() if comment else "",
                    reporter_hash=f"session_{st.session_state.get('user_id', 1)}",
                    status="pending",
                    priority_score=1.5 if saved_image_path else 1.0,
                    auto_checks_json={
                        "is_plausible": check.is_plausible,
                        "flags": check.flags,
                        "has_image": saved_image_path is not None,
                    }
                )
                db.add(rep)
                db.commit()
                db.refresh(rep)

                st.success(
                    f"✓ Report #{rep.id} submitted successfully! Our verification queue will review your submission."
                )
                if check.flags:
                    st.info(f"Note from auto-checker: {', '.join(check.flags)}")
            finally:
                db.close()
