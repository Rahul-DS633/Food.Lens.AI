"""
FoodLens AI — Family Profiles & Household Dietary Management
Multi-person allergen shields, DPDP Act minor safety compliance, and collaborative food literacy.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st

st.set_page_config(page_title="Family Profiles — FoodLens AI", page_icon="👨‍👩‍👧‍👦", layout="wide")

CSS_PATH = Path(__file__).parent.parent / "assets" / "theme.css"
if CSS_PATH.exists():
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from db.session import SessionLocal, export_household_data, delete_household_data
from db.models import Household, HouseholdMember
from app.components.icons import get_icon_svg
from app.components.sidebar import render_sidebar
from app.components.page_header import render_page_header

render_sidebar("Family")

USER_ID = st.session_state.get("user_id", 1)

ALLERGEN_OPTIONS = [
    "milk", "egg", "peanut", "tree nuts", "soy", "wheat/gluten",
    "sesame", "fish", "shellfish", "mustard"
]

DIETARY_PREF_OPTIONS = ["vegetarian", "vegan", "jain", "halal"]
AVATAR_OPTIONS = ["👨", "👩", "👧", "👦", "👵", "👴", "👶", "🧑", "🧒", "🧓"]

render_page_header(
    title="Family Dietary Profiles",
    subtitle="Manage allergy shields and portion sizes for everyone in your home. Check one scan for the whole family.",
    icon_name="users",
    overline="MULTI-MEMBER HOUSEHOLD SHIELD",
    action_pills=[
        {"icon": "users", "text": "Multi-User Safety"},
        {"icon": "shield", "text": "Age-Scaled Portions"}
    ]
)

db = SessionLocal()
try:
    hh = db.query(Household).filter(Household.owner_user_id == USER_ID).first()
    if not hh:
        hh = Household(owner_user_id=USER_ID)
        db.add(hh)
        db.commit()
        db.refresh(hh)

    members = hh.members

    # Top Status Bar
    col_stat1, col_stat2 = st.columns([3, 1.2])
    with col_stat1:
        st.markdown(
            f"""
            <div style="font-size: 14.5px; color: #334155;">
                Active Household Members: <b>{len(members)} / 8</b>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_stat2:
        exp_data = export_household_data(USER_ID, db)
        if exp_data and exp_data.get("members"):
            st.download_button(
                "📥 Export Household Data (JSON)",
                data=json.dumps(exp_data, indent=2),
                file_name=f"foodlens_family_export_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                width="stretch",
            )

    st.markdown("---")

    # Member Showcase Cards
    if members:
        cols = st.columns(min(len(members), 4))
        for idx, m in enumerate(members):
            with cols[idx % 4]:
                minor_badge = " • <span style='color: #0369A1; font-weight: 700;'>Minor (<18)</span>" if m.is_minor else ""
                allergies_str = ", ".join(m.allergies_json) if m.allergies_json else "None"
                prefs_str = ", ".join(m.dietary_prefs_json) if m.dietary_prefs_json else "None"

                st.markdown(
                    f"""
                    <div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 14px; padding: 16px; margin-bottom: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
                        <div style="font-size: 32px; margin-bottom: 6px;">{m.emoji_avatar}</div>
                        <div style="font-size: 17px; font-weight: 800; color: #0F172A;">{m.display_name}</div>
                        <div style="font-size: 13px; color: #64748B; margin-bottom: 8px;">Age: {m.age}{minor_badge}</div>
                        <div style="font-size: 12px; color: #475569; line-height: 1.5;">
                            🛡️ <b>Allergies:</b> <span style="color: #991B1B; font-weight: 600;">{allergies_str}</span><br>
                            🥗 <b>Diet:</b> <span style="text-transform: capitalize;">{prefs_str}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if st.button(f"Remove {m.display_name}", key=f"del_mem_{m.id}"):
                    db.delete(m)
                    db.commit()
                    st.success(f"Removed {m.display_name}.")
                    st.rerun()

    else:
        st.markdown(
            """
            <div style="background: #F0FDF4; border: 1.5px solid #86EFAC; border-radius: 12px; padding: 14px 18px; margin-bottom: 14px; color: #144730; font-size: 14px; display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 18px;">ℹ️</span>
                <span><b>No family members added yet.</b> Add your first member below to activate multi-person food checks!</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    # Add Member Form
    if len(members) < 8:
        with st.expander("➕ Add a Family Member", expanded=(len(members) == 0)):
            col_av, col_nm, col_ag = st.columns([1, 2, 1])
            with col_av:
                avatar = st.selectbox("Avatar", AVATAR_OPTIONS, index=0)
            with col_nm:
                name = st.text_input("Name or Nickname", placeholder="e.g. Aarav, Dadi, Little Sis")
            with col_ag:
                age = st.number_input("Age (Years)", min_value=1, max_value=120, value=25)

            is_minor = age < 18
            weight_val = None

            if is_minor:
                st.markdown(
                    """
                    <div style="background: #EFF6FF; border: 1.5px solid #93C5FD; border-radius: 10px; padding: 10px 14px; margin-bottom: 12px; font-size: 13px; color: #1E40AF;">
                        <b>Child Data Protection (India DPDP Act 2023):</b><br>
                        Caloric and weight guidance are strictly disabled for individuals under 18. FoodLens will provide allergen alerts and general nutritional facts only.
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                consent = st.checkbox(
                    "I confirm I am the parent or lawful guardian of this child and consent to processing dietary preferences for food safety.",
                    value=True,
                    key="child_consent"
                )
            else:
                col_wt, col_empty = st.columns([1, 1])
                with col_wt:
                    weight_val = st.number_input("Weight in kg (Optional)", min_value=5.0, max_value=300.0, value=65.0)
                consent = st.checkbox(
                    "I confirm I have this person's permission to record their dietary profile.",
                    value=True,
                    key="adult_consent"
                )

            selected_allergies = st.multiselect("Allergens to Avoid", options=ALLERGEN_OPTIONS)
            selected_prefs = st.multiselect("Dietary Preferences", options=DIETARY_PREF_OPTIONS)

            if st.button("Save Family Member", type="primary"):
                if not name or not name.strip():
                    st.error("Please enter a name for the family member.")
                elif not consent:
                    st.error("Consent confirmation is required.")
                else:
                    new_m = HouseholdMember(
                        household_id=hh.id,
                        display_name=name.strip(),
                        emoji_avatar=avatar,
                        age=age,
                        weight_kg=weight_val if not is_minor else None,
                        allergies_json=selected_allergies,
                        dietary_prefs_json=selected_prefs,
                        is_minor=is_minor,
                        consent_by_owner=consent,
                        consent_at=datetime.now(timezone.utc),
                    )
                    db.add(new_m)
                    db.commit()
                    st.success(f"Added {name} to your household!")
                    st.rerun()
    else:
        st.warning("Household limit of 8 members reached. Remove a profile to add another.")

    st.markdown("---")

    # Danger Zone / Data Erasure
    with st.expander("⚠️ Data Privacy & Household Erasure (DPDP Act)"):
        st.markdown(
            """
            Under India's Digital Personal Data Protection Act (2023), you have the absolute right to erasure. 
            Deleting your household permanently deletes all member profiles, dietary preferences, and allergy matrices.
            """
        )
        if st.button("Delete Entire Household & All Profiles", type="secondary"):
            delete_household_data(USER_ID, db)
            st.success("Household data deleted completely.")
            st.rerun()

finally:
    db.close()
