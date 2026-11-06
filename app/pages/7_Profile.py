"""
FoodLens AI — Personalized Dietary Profile & Privacy Controls
Supports Guest Mode (session-only) and Account Mode (local device storage)
in full compliance with India's DPDP Act 2023.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st

st.set_page_config(page_title="My Dietary Profile — FoodLens AI", page_icon="🛡️", layout="wide")

CSS_PATH = Path(__file__).parent.parent / "assets" / "theme.css"
if CSS_PATH.exists():
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from db.session import SessionLocal, export_user_data, delete_user_data
from db.models import User, UserProfile, Achievement, UserAchievement, utcnow
from app.components.icons import get_icon_svg

if "user_id" not in st.session_state:
    st.session_state.user_id = 1
if "language" not in st.session_state:
    st.session_state.language = "en"
if "user_profile" not in st.session_state:
    st.session_state.user_profile = None

# Header with vector iconography
shield_icon = get_icon_svg("shield", size=28, color="#1B5E3F")
st.markdown(
    f"""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 6px;">
        {shield_icon}
        <h1 style="margin: 0; color: #144730; font-size: 26px;">Personalized Food Fit Profile</h1>
    </div>
    <p style="color: #64748B; font-size: 14px; margin-bottom: 20px;">
        Configure your dietary preferences and allergen alerts. Packaged foods will be evaluated against your profile.
    </p>
    """,
    unsafe_allow_html=True
)

# Load existing profile from DB or session
db = SessionLocal()
existing_db_profile = None
try:
    existing_db_profile = db.query(UserProfile).filter(UserProfile.user_id == st.session_state.user_id).first()
finally:
    db.close()

# Prefill values
curr_profile = st.session_state.user_profile
if not curr_profile and existing_db_profile:
    curr_profile = {
        "name": existing_db_profile.name,
        "age": existing_db_profile.age,
        "weight_kg": existing_db_profile.weight_kg,
        "allergies": existing_db_profile.allergies_json or [],
        "custom_allergens": existing_db_profile.custom_allergens_text or "",
        "consent_given": existing_db_profile.consent_given,
        "parental_consent_given": existing_db_profile.parental_consent_given,
        "is_guest": False,
    }
    st.session_state.user_profile = curr_profile

curr_profile = curr_profile or {}

col_form, col_privacy = st.columns([3, 2], gap="large")

with col_form:
    st.markdown("### 1. Storage Mode")
    storage_mode = st.radio(
        "Select Profile Mode",
        ["Account Mode (Saved to this device)", "Guest Mode (Current browser session only — zero disk storage)"],
        index=1 if curr_profile.get("is_guest") else 0
    )
    is_guest = "Guest Mode" in storage_mode

    st.markdown("### 2. Basic Information")
    name = st.text_input(
        "Display Name",
        value=curr_profile.get("name", "Curious Eater"),
        help="Used only on your local screen. Your name is NEVER transmitted to AI or external servers."
    )

    age = st.number_input(
        "Age (Years)",
        min_value=1,
        max_value=120,
        value=int(curr_profile.get("age", 25)),
        help="Ages under 18 have calorie and weight-based guidance disabled under safety guidelines."
    )

    is_minor = age < 18
    if is_minor:
        st.info("ℹ️ **Under-18 Safety Guardrail**: Calorie and weight-based guidance are automatically disabled.")

    has_weight = st.checkbox(
        "Provide weight (Optional, for adult protein RDA calculation)",
        value=bool(curr_profile.get("weight_kg")),
        disabled=is_minor
    )
    weight_kg = None
    if has_weight and not is_minor:
        weight_kg = st.number_input(
            "Weight (kg)",
            min_value=5.0,
            max_value=300.0,
            value=float(curr_profile.get("weight_kg") or 65.0),
            step=0.5,
            help="Used only to scale adult ICMR-NIN protein reference target (0.83 g/kg). Never used for weight-loss goals."
        )

    st.markdown("### 3. Allergen Safety Triggers")
    st.caption("Select any allergens you want FoodLens to flag with red alerts upon scanning:")

    ALLERGEN_OPTIONS = {
        "milk": "Milk & Dairy (Butter, Ghee, Paneer, Whey, Casein)",
        "wheat_gluten": "Wheat & Gluten (Atta, Maida, Sooji, Rava, Semolina)",
        "peanut": "Peanuts / Groundnuts (Moongphali, Arachis oil)",
        "tree_nuts": "Tree Nuts (Almond, Cashew, Walnut, Pistachio)",
        "soy": "Soy & Derivatives (Soya, Soy Lecithin, INS 322)",
        "egg": "Eggs (Egg powder, Albumin, Anda)",
        "sesame": "Sesame (Til, Gingelly, Tahini)",
        "mustard": "Mustard (Sarson, Rai)",
        "fish": "Fish (Machhli)",
        "shellfish": "Shellfish / Crustaceans (Prawns, Shrimp, Jhinga)",
    }

    selected_allergies = st.multiselect(
        "Standard Common Allergens",
        options=list(ALLERGEN_OPTIONS.keys()),
        default=curr_profile.get("allergies", []),
        format_func=lambda x: ALLERGEN_OPTIONS.get(x, x)
    )

    custom_allergens = st.text_input(
        "Custom Allergen / Ingredient Triggers (comma-separated)",
        value=curr_profile.get("custom_allergens", ""),
        placeholder="e.g. Monosodium Glutamate, Preservative 220, Palm Oil"
    )

    st.markdown("### 4. Consent & Privacy Agreement")
    consent_given = st.checkbox(
        "I consent to FoodLens processing my dietary preferences and allergen selections to evaluate packaged food labels.",
        value=bool(curr_profile.get("consent_given", False))
    )

    parental_consent_given = False
    if is_minor:
        st.markdown(
            """
            <div style="background: #FEF3C7; border: 1.5px solid #F59E0B; border-radius: 10px; padding: 12px 14px; margin-bottom: 8px;">
                <b style="color: #92400E;">DPDP Act Notice for Minors (Under 18):</b>
                <p style="color: #78350F; font-size: 12.5px; margin: 4px 0 0 0;">
                    Under Section 9 of the Digital Personal Data Protection Act 2023, personal data of children requires verifiable parental consent.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        parental_consent_given = st.checkbox(
            "I confirm that I am a parent or legal guardian, or have verifiable parental permission to configure this profile.",
            value=bool(curr_profile.get("parental_consent_given", False))
        )

    if st.button("Save Profile & Enable Personal Fit", type="primary", width="stretch"):
        if not consent_given:
            st.error("Please check the consent box to enable personalized food analysis.")
        elif is_minor and not parental_consent_given:
            st.error("Parental/guardian verification is required for users under 18.")
        else:
            profile_dict = {
                "name": name.strip(),
                "age": int(age),
                "weight_kg": weight_kg if (has_weight and not is_minor) else None,
                "allergies": selected_allergies,
                "custom_allergens": custom_allergens.strip(),
                "consent_given": consent_given,
                "parental_consent_given": parental_consent_given,
                "is_guest": is_guest,
            }
            st.session_state.user_profile = profile_dict

            if not is_guest:
                db = SessionLocal()
                try:
                    user = db.query(User).filter(User.id == st.session_state.user_id).first()
                    if not user:
                        user = User(id=st.session_state.user_id, display_name=name)
                        db.add(user)
                        db.flush()

                    db_prof = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
                    if not db_prof:
                        db_prof = UserProfile(
                            user_id=user.id,
                            name=name,
                            age=int(age),
                            weight_kg=weight_kg if (has_weight and not is_minor) else None,
                            allergies_json=selected_allergies,
                            custom_allergens_text=custom_allergens.strip(),
                            consent_given=consent_given,
                            parental_consent_given=parental_consent_given,
                            consent_timestamp=utcnow(),
                        )
                        db.add(db_prof)
                    else:
                        db_prof.name = name
                        db_prof.age = int(age)
                        db_prof.weight_kg = weight_kg if (has_weight and not is_minor) else None
                        db_prof.allergies_json = selected_allergies
                        db_prof.custom_allergens_text = custom_allergens.strip()
                        db_prof.consent_given = consent_given
                        db_prof.parental_consent_given = parental_consent_given
                        db_prof.updated_at = utcnow()

                    # Award "PROFILE_SET_UP" badge
                    ach = db.query(Achievement).filter(Achievement.code == "PROFILE_SET_UP").first()
                    if ach:
                        existing_ach = db.query(UserAchievement).filter(
                            UserAchievement.user_id == user.id,
                            UserAchievement.achievement_id == ach.id
                        ).first()
                        if not existing_ach:
                            db.add(UserAchievement(user_id=user.id, achievement_id=ach.id))

                    db.commit()
                finally:
                    db.close()

            st.success("🎉 Profile updated! Scans and product reviews will now show your Personalized Food Fit.")
            st.rerun()

with col_privacy:
    st.markdown("### Privacy & Safeguards")
    st.markdown(
        """
        <div class="foodlens-card-3d">
            <h4 style="color: #144730; margin-top: 0; font-size: 15px;">🛡️ Our Privacy Commitments</h4>
            <ul style="font-size: 13px; line-height: 1.6; color: #334155; padding-left: 18px; margin-bottom: 16px;">
                <li><b>Name Privacy:</b> Your name stays on this device. It is NEVER transmitted to external AI models.</li>
                <li><b>No Medical Claims:</b> FoodLens provides nutritional education and label transparency, not clinical advice.</li>
                <li><b>No Eating Disorder Profiling:</b> We never set weight-loss targets, calorie restriction goals, or BMI labels.</li>
                <li><b>Deterministic Allergen Detection:</b> 100% pure Python pattern matching against label text. Never hallucinated.</li>
                <li><b>India DPDP Act Ready:</b> You have full rights to export or permanently delete your data at any time.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### Manage My Data (DPDP Act)")
    col_exp, col_del = st.columns(2)

    with col_exp:
        db = SessionLocal()
        try:
            exp_data = export_user_data(st.session_state.user_id, db)
        finally:
            db.close()

        st.download_button(
            "📥 Export My Data (JSON)",
            data=json.dumps(exp_data, indent=2),
            file_name=f"foodlens_profile_{st.session_state.user_id}.json",
            mime="application/json",
            width="stretch"
        )

    with col_del:
        if st.button("🗑️ Delete My Data", type="secondary", width="stretch"):
            db = SessionLocal()
            try:
                delete_user_data(st.session_state.user_id, db)
            finally:
                db.close()
            st.session_state.user_profile = None
            st.success("All personal data has been erased.")
            st.rerun()
