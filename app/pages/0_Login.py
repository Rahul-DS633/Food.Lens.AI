"""
FoodLens AI — Member & Administrator Authentication Portal
Provides secure credential sign-in, user registration with DPDP Act 2023 consent,
quick demo profile switching, and administrator review queue access.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st

st.set_page_config(
    page_title="Login & Access — FoodLens AI",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load theme CSS
CSS_PATH = Path(__file__).parent.parent / "assets" / "theme.css"
if CSS_PATH.exists():
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.html(f"<style>{f.read()}</style>")

from db.session import SessionLocal, init_db
from db.models import User, UserProfile, UserProgress
from foodlens.auth import (
    authenticate_user,
    register_user,
    verify_admin_key,
    hash_password,
)
from foodlens.gamification.xp import get_level_for_xp
from app.components.sidebar import render_sidebar
from app.components.page_header import render_page_header

# Ensure database tables exist
try:
    init_db()
except Exception:
    pass

# Initialize session state variables
if "user_id" not in st.session_state:
    st.session_state.user_id = 1
if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = False
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False
if "user_role" not in st.session_state:
    st.session_state.user_role = "user"

render_sidebar("Login")

# Render Emerald Hero Banner
render_page_header(
    title="Account & Admin Login",
    subtitle="Sign in to your FoodLens personal health profile, manage family accounts, or enter the admin verification console.",
    icon_name="lock",
    emoji="🔐",
    overline="AUTHENTICATION & IDENTITY",
    action_pills=[
        {"icon": "lock", "text": "Secure Sign-In"},
        {"icon": "shield", "text": "DPDP 2023 Shield"},
        {"icon": "check_circle", "text": "Role-Based Access"}
    ]
)

db = SessionLocal()

try:
    current_user = db.query(User).filter(User.id == st.session_state.user_id).first()
    current_profile = current_user.profile if current_user else None
    current_progress = current_user.progress if current_user else None
    current_role = getattr(current_user, "role", "user") if current_user else "user"
    is_admin_active = st.session_state.get("admin_authenticated", False) or (current_role == "admin")

    # 1. Active Session Status Card
    if st.session_state.get("is_logged_in", False) or is_admin_active:
        user_name = current_user.display_name if current_user else "FoodLens User"
        handle = f"@{current_user.username}" if current_user and current_user.username else "@user"
        user_xp = current_progress.xp if current_progress else 25
        lvl_name, lvl_icon, _, _ = get_level_for_xp(user_xp)
        streak = current_progress.current_streak if current_progress else 1
        allergens = current_profile.allergies_json if current_profile and current_profile.allergies_json else []
        allergen_str = ", ".join(allergens) if allergens else "None specified"

        role_badge = (
            '<span style="background: #DC2626; color: white; padding: 3px 9px; border-radius: 9999px; font-size: 11px; font-weight: 800;">🛡️ ADMINISTRATOR</span>'
            if is_admin_active
            else '<span style="background: #DCFCE7; color: #166534; padding: 3px 9px; border-radius: 9999px; font-size: 11px; font-weight: 800;">👤 VERIFIED MEMBER</span>'
        )

        st.html(
            f"""
            <div style="
                background: #FFFFFF;
                border: 2px solid #86EFAC;
                border-radius: 16px;
                padding: 18px 22px;
                margin-bottom: 22px;
                box-shadow: 0 4px 14px rgba(22, 101, 52, 0.08);
            ">
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
                    <div style="display: flex; align-items: center; gap: 14px;">
                        <div style="
                            width: 52px; height: 52px;
                            border-radius: 50%;
                            background: linear-gradient(135deg, #166534, #22C55E);
                            display: flex; align-items: center; justify-content: center;
                            font-size: 24px; color: white;
                            box-shadow: 0 4px 10px rgba(22, 101, 52, 0.25);
                        ">
                            {"🛡️" if is_admin_active else "👤"}
                        </div>
                        <div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="font-size: 18px; font-weight: 800; color: #0F172A;">{user_name}</span>
                                <span style="font-size: 13px; color: #64748B; font-weight: 600;">{handle}</span>
                                {role_badge}
                            </div>
                            <div style="font-size: 13px; color: #334155; margin-top: 3px;">
                                <strong>Level:</strong> {lvl_icon} {lvl_name} &nbsp;•&nbsp; 
                                <strong>Streak:</strong> 🔥 {streak} days &nbsp;•&nbsp; 
                                <strong>XP:</strong> ⚡ {user_xp} &nbsp;•&nbsp; 
                                <strong>Dietary Shield:</strong> 🛡️ {allergen_str}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """
        )

        # Quick action row for logged-in user
        c_act1, c_act2, c_act3, c_act4 = st.columns([1.2, 1.2, 1.2, 1])
        with c_act1:
            if st.button("📷 Open Scanner", type="primary", use_container_width=True):
                st.switch_page("pages/1_Scan.py")
        with c_act2:
            if st.button("👤 Dietary Profile", use_container_width=True):
                st.switch_page("pages/7_Profile.py")
        with c_act3:
            if is_admin_active:
                if st.button("🛡️ Admin Review Queue", use_container_width=True):
                    st.switch_page("pages/9_Admin.py")
            else:
                if st.button("⚖️ Compare Products", use_container_width=True):
                    st.switch_page("pages/3_Compare.py")
        with c_act4:
            if st.button("🚪 Sign Out", use_container_width=True):
                st.session_state.is_logged_in = False
                st.session_state.admin_authenticated = False
                st.session_state.user_role = "user"
                st.session_state.user_profile = None
                st.success("Signed out successfully.")
                st.rerun()

        st.markdown("---")

    # 2. Main Login / Registration / Admin Interface Tabs
    tab_signin, tab_register, tab_admin, tab_demo = st.tabs([
        "👤 Member Sign-In",
        "📝 Create Account (DPDP Consent)",
        "🛡️ Admin Console",
        "⚡ Quick Demo Switcher"
    ])

    # --- TAB 1: Member Sign-In ---
    with tab_signin:
        st.markdown("### 👤 Sign In with Credentials")
        st.markdown("Enter your FoodLens username or email to restore your personalized dietary shield and quest achievements.")

        c_log1, c_log2 = st.columns([2, 1], gap="large")
        with c_log1:
            with st.form("user_login_form"):
                identifier = st.text_input("Username or Email", placeholder="e.g. curious or curious@foodlens.ai")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submitted = st.form_submit_button("Sign In to FoodLens", type="primary", use_container_width=True)

                if submitted:
                    if not identifier or not password:
                        st.error("Please enter both username/email and password.")
                    else:
                        authenticated_user = authenticate_user(db, identifier, password)
                        if authenticated_user:
                            st.session_state.user_id = authenticated_user.id
                            st.session_state.is_logged_in = True
                            auth_role = getattr(authenticated_user, "role", "user")
                            st.session_state.user_role = auth_role
                            if auth_role == "admin":
                                st.session_state.admin_authenticated = True

                            # Sync profile in session
                            prof = authenticated_user.profile
                            if prof:
                                st.session_state.user_profile = {
                                    "name": prof.name,
                                    "age": prof.age,
                                    "weight_kg": prof.weight_kg,
                                    "allergies": prof.allergies_json or [],
                                    "custom_allergens": prof.custom_allergens_text or "",
                                    "consent_given": prof.consent_given,
                                    "parental_consent_given": prof.parental_consent_given,
                                    "is_guest": False,
                                }
                            st.toast(f"Welcome back, {authenticated_user.display_name}! 🥗", icon="🎉")
                            st.rerun()
                        else:
                            st.error("Invalid username/email or password. Please check your credentials or use the Quick Switcher.")

        with c_log2:
            st.html(
                """
                <div style="
                    background: #F8FAFC;
                    border: 1px solid #CBD5E1;
                    border-radius: 12px;
                    padding: 16px;
                    font-size: 13px;
                    color: #475569;
                ">
                    <div style="font-weight: 800; color: #0F172A; margin-bottom: 8px; font-size: 14px;">
                        🔒 Privacy-First Architecture
                    </div>
                    <ul style="padding-left: 18px; margin: 0; line-height: 1.6;">
                        <li>All nutrient calculations run on pure deterministic code.</li>
                        <li>Health & dietary triggers are stored strictly locally on your device.</li>
                        <li>Full compliance with India's <strong>DPDP Act 2023</strong>.</li>
                        <li>Default demo login: <code>curious</code> / <code>demo123</code>.</li>
                    </ul>
                </div>
                """
            )

    # --- TAB 2: Register New Account ---
    with tab_register:
        st.markdown("### 📝 Register New FoodLens Account")
        st.markdown("Create a personalized food profile. Your personal health metrics are used solely for real-time safety alerts.")

        with st.form("user_registration_form"):
            r_col1, r_col2 = st.columns(2)
            with r_col1:
                new_username = st.text_input("Username (alphanumeric)", placeholder="e.g. rahul_fit")
                new_display_name = st.text_input("Display Name", placeholder="e.g. Rahul Sharma")
                new_email = st.text_input("Email (Optional)", placeholder="e.g. rahul@example.com")
            with r_col2:
                new_password = st.text_input("Choose Password (min 4 characters)", type="password")
                new_password_confirm = st.text_input("Confirm Password", type="password")
                new_age = st.number_input("Age (Years)", min_value=1, max_value=120, value=25)

            st.markdown("#### 🛡️ Dietary Triggers & Allergens")
            ALLERGEN_CHOICES = [
                "Peanuts", "Tree Nuts", "Milk / Dairy", "Gluten / Wheat",
                "Soybeans", "Egg", "Fish", "Crustaceans / Shellfish",
                "Sesame", "Mustard", "Sulfites", "Lactose"
            ]
            selected_allergens = st.multiselect(
                "Select ingredients you want FoodLens to flag during scans",
                ALLERGEN_CHOICES,
                default=[]
            )
            custom_allergens = st.text_input(
                "Custom Triggers / Sensitivities (comma-separated)",
                placeholder="e.g. artificial sweeteners, palm oil, MSG, caffeine"
            )

            st.markdown("#### 📜 DPDP Act 2023 Consent & Transparency")
            consent_box = st.checkbox(
                "I give explicit consent under India's Digital Personal Data Protection (DPDP) Act 2023 for FoodLens to process my dietary and allergy preferences locally on this device for real-time safety warnings.",
                value=True
            )
            parental_consent_box = False
            if new_age < 18:
                parental_consent_box = st.checkbox(
                    "Parental/Guardian Consent: As parent/guardian, I authorize the collection of dietary preferences for this minor user.",
                    value=False
                )

            reg_submitted = st.form_submit_button("Create Profile & Sign In (+25 XP)", type="primary", use_container_width=True)

            if reg_submitted:
                if not new_username or not new_password:
                    st.error("Username and password are required.")
                elif new_password != new_password_confirm:
                    st.error("Passwords do not match.")
                elif not consent_box:
                    st.error("Consent is required under DPDP Act 2023 to save dietary preferences.")
                elif new_age < 18 and not parental_consent_box:
                    st.error("Parental/guardian consent is required for users under 18.")
                else:
                    try:
                        registered = register_user(
                            db=db,
                            username=new_username,
                            password=new_password,
                            display_name=new_display_name,
                            email=new_email,
                            age=int(new_age),
                            allergies=[a.lower() for a in selected_allergens],
                            custom_allergens=custom_allergens,
                            consent_given=consent_box,
                            parental_consent_given=parental_consent_box,
                            role="user"
                        )
                        st.session_state.user_id = registered.id
                        st.session_state.is_logged_in = True
                        st.session_state.user_role = "user"
                        st.session_state.admin_authenticated = False
                        st.session_state.user_profile = {
                            "name": registered.display_name,
                            "age": new_age,
                            "allergies": [a.lower() for a in selected_allergens],
                            "custom_allergens": custom_allergens,
                            "consent_given": True,
                            "is_guest": False
                        }
                        st.balloons()
                        st.toast(f"Account created! Welcome, {registered.display_name}! 🎉", icon="🛡️")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Registration error: {e}")

    # --- TAB 3: Admin Console ---
    with tab_admin:
        st.markdown("### 🛡️ Administrator Verification Access")
        st.markdown("Restricted portal for food safety auditors, regulatory reviewers, and catalog managers.")

        ad_col1, ad_col2 = st.columns([2, 1], gap="large")
        with ad_col1:
            with st.form("admin_login_form"):
                admin_key_input = st.text_input(
                    "Admin Master Key / Password",
                    type="password",
                    placeholder="Enter administrative credentials"
                )
                admin_submit = st.form_submit_button("Verify & Enter Admin Console", type="primary", use_container_width=True)

                if admin_submit:
                    if verify_admin_key(admin_key_input):
                        st.session_state.admin_authenticated = True
                        st.session_state.user_role = "admin"

                        # Link to admin user record if available
                        admin_user = db.query(User).filter(User.role == "admin").first()
                        if admin_user:
                            st.session_state.user_id = admin_user.id
                            st.session_state.is_logged_in = True

                        st.success("✅ Administrative access verified!")
                        st.toast("Admin session active. Redirecting...", icon="🛡️")
                        st.rerun()
                    else:
                        st.error("Invalid administrator key or password.")

            if st.session_state.get("admin_authenticated", False):
                st.html(
                    """
                    <div style="background: #F0FDF4; border: 1.5px solid #22C55E; border-radius: 12px; padding: 14px; margin-top: 14px;">
                        <span style="font-weight: 800; color: #166534; font-size: 15px;">🛡️ Administrator Session Currently Active</span>
                        <p style="margin: 4px 0 0 0; font-size: 13px; color: #15803D;">You have full privileges to review data reports, inspect submitted OCR images, and approve verified revisions.</p>
                    </div>
                    """
                )
                if st.button("🚀 Proceed to Admin Review Queue", type="primary", use_container_width=True):
                    st.switch_page("pages/9_Admin.py")

        with ad_col2:
            st.html(
                """
                <div style="
                    background: #FEF2F2;
                    border: 1px solid #FECACA;
                    border-radius: 12px;
                    padding: 16px;
                    font-size: 13px;
                    color: #991B1B;
                ">
                    <div style="font-weight: 800; font-size: 14px; margin-bottom: 6px;">
                        🛡️ Admin Capabilities
                    </div>
                    <ul style="padding-left: 18px; margin: 0; line-height: 1.6;">
                        <li>Audit user-flagged label errors and OCR mismatches.</li>
                        <li>Inspect high-resolution image crops.</li>
                        <li>Publish immutable product revisions with FSSAI compliance notes.</li>
                        <li>Default demo key: <code>foodlens_admin_secret</code>.</li>
                    </ul>
                </div>
                """
            )

    # --- TAB 4: Quick Demo Profile Switcher ---
    with tab_demo:
        st.markdown("### ⚡ Quick Demo Persona Switcher")
        st.markdown("Instantly switch between pre-configured user personas to test personalized warnings, sugar metrics, and gamification tiers.")

        all_users = db.query(User).order_by(User.id.asc()).all()

        for u in all_users:
            u_prof = u.profile
            u_prog = u.progress
            u_xp = u_prog.xp if u_prog else 25
            u_lvl, u_icon, _, _ = get_level_for_xp(u_xp)
            u_allergens = u_prof.allergies_json if u_prof and u_prof.allergies_json else []
            allergen_preview = ", ".join(u_allergens) if u_allergens else "None"
            is_active = (u.id == st.session_state.user_id)

            col_u_info, col_u_btn = st.columns([3, 1])
            with col_u_info:
                st.html(
                    f"""
                    <div style="
                        background: {'#F0FDF4' if is_active else '#FFFFFF'};
                        border: 1.5px solid {'#4ADE80' if is_active else '#E2E8F0'};
                        border-radius: 12px;
                        padding: 10px 14px;
                        margin-bottom: 8px;
                    ">
                        <div style="display: flex; align-items: center; justify-content: space-between;">
                            <div>
                                <strong style="color: #0F172A; font-size: 14px;">{u.display_name}</strong>
                                <span style="font-size: 12px; color: #64748B;">(@{u.username or 'user'})</span>
                                {'<span style="background: #166534; color: white; padding: 1px 6px; border-radius: 4px; font-size: 10px; font-weight: 800; margin-left: 6px;">CURRENT</span>' if is_active else ''}
                            </div>
                            <span style="font-size: 12px; font-weight: 700; color: #166534;">{u_icon} {u_lvl} ({u_xp} XP)</span>
                        </div>
                        <div style="font-size: 12px; color: #475569; margin-top: 2px;">
                            <strong>Role:</strong> {getattr(u, "role", "user")} &nbsp;|&nbsp; <strong>Allergies:</strong> {allergen_preview}
                        </div>
                    </div>
                    """
                )
            with col_u_btn:
                if st.button(f"Switch to #{u.id}", key=f"switch_user_{u.id}", disabled=is_active, use_container_width=True):
                    st.session_state.user_id = u.id
                    st.session_state.is_logged_in = True
                    u_role = getattr(u, "role", "user")
                    st.session_state.user_role = u_role
                    st.session_state.admin_authenticated = (u_role == "admin")
                    if u_prof:
                        st.session_state.user_profile = {
                            "name": u_prof.name,
                            "age": u_prof.age,
                            "weight_kg": u_prof.weight_kg,
                            "allergies": u_prof.allergies_json or [],
                            "custom_allergens": u_prof.custom_allergens_text or "",
                            "consent_given": u_prof.consent_given,
                            "is_guest": False
                        }
                    st.toast(f"Switched active user to {u.display_name}! 👤", icon="✅")
                    st.rerun()

finally:
    db.close()

