"""
FoodLens AI — Custom Sidebar Component
Provides ultra-premium branding, user level & XP stats, quick actions,
and compliance badges for the Streamlit sidebar.
"""

from typing import Optional
import streamlit as st
from db.models import Base, Household, User
from db.session import SessionLocal, init_db, engine
from foodlens.gamification.xp import get_level_for_xp


def render_sidebar(active_page: Optional[str] = None) -> None:
    """
    Renders top branding, user quest status, and footer badges in st.sidebar.
    """
    with st.sidebar:
        # Force suppress any unwanted section header or stray 'key' header in Streamlit nav
        st.markdown(
            """
            <style>
            [data-testid="stNavSectionHeader"],
            [data-testid="stNavSectionHeader"] *,
            [data-testid="stSidebarNavSectionHeader"],
            [data-testid="stSidebarNav"] header,
            [data-testid="stSidebarNav"] header *,
            [data-testid="stSidebarNav"] .en0apyo9,
            [data-testid="stSidebarNav"] .en0apyo8,
            [data-testid="stSidebarNav"] .en0apyo12,
            section[data-testid="stSidebar"] header,
            section[data-testid="stSidebar"] header *,
            section[data-testid="stSidebar"] .en0apyo9,
            section[data-testid="stSidebar"] .en0apyo8,
            section[data-testid="stSidebar"] .en0apyo12 {
                display: none !important;
                visibility: hidden !important;
                height: 0 !important;
                min-height: 0 !important;
                max-height: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
                font-size: 0 !important;
                line-height: 0 !important;
                overflow: hidden !important;
                opacity: 0 !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # 1. Top Brand Logo & Title Card
        st.markdown(
            """
            <div style="
                background: linear-gradient(135deg, #144730 0%, #1B5E3F 60%, #2E7D56 100%);
                border-radius: 16px;
                padding: 16px;
                margin-bottom: 14px;
                box-shadow: 0 8px 24px rgba(20, 71, 48, 0.22);
                border: 1px solid #4ADE80;
                position: relative;
                overflow: hidden;
            ">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 26px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));">🥗</span>
                        <span style="font-weight: 800; font-size: 19px; color: #FFFFFF; letter-spacing: -0.3px;">FoodLens AI</span>
                    </div>
                    <span style="
                        background: rgba(163, 230, 53, 0.22);
                        color: #A3E635;
                        border: 1px solid rgba(163, 230, 53, 0.4);
                        font-size: 10px;
                        font-weight: 800;
                        padding: 2px 7px;
                        border-radius: 6px;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                    ">Pro v1.0</span>
                </div>
                <div style="color: #D1FAE5; font-size: 12px; font-weight: 500; margin-top: 2px;">
                    Packaged Food Intelligence Engine
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 2. User Level & Quest Mini-Card
        db = SessionLocal()
        try:
            user_id = st.session_state.get("user_id", 1)
            user = None
            progress = None
            profile = None
            household = None

            try:
                user = db.query(User).filter(User.id == user_id).first()
                progress = user.progress if user else None
                profile = user.profile if user else None
                household = db.query(Household).filter(Household.owner_user_id == user_id).first()
            except Exception:
                try:
                    Base.metadata.create_all(bind=engine)
                    init_db()
                    user = db.query(User).filter(User.id == user_id).first()
                    progress = user.progress if user else None
                    profile = user.profile if user else None
                    household = db.query(Household).filter(Household.owner_user_id == user_id).first()
                except Exception:
                    user = None
                    progress = None
                    profile = None
                    household = None

            xp = progress.xp if progress else 25
            streak = progress.current_streak if progress else 1
            lvl_name, lvl_icon, base_xp, next_xp = get_level_for_xp(xp)
            user_name = profile.name if profile and profile.name else "You"
            user_role = getattr(user, "role", "user") if user else "user"
            is_admin = st.session_state.get("admin_authenticated", False) or (user_role == "admin")
            avatar = "🛡️" if is_admin else "👤"
            badge_text = "🛡️ Admin" if is_admin else f"{lvl_icon} {lvl_name}"
            badge_color = "#DC2626" if is_admin else "#166534"
            members_count = len(household.members) if household and household.members else 0

            # Level progress percentage
            pct = 0.0
            span = max(1, next_xp - base_xp)
            pct = min(1.0, max(0.0, (xp - base_xp) / span))
            pct_bar = int(pct * 100)

            st.markdown(
                f"""
                <div style="
                    background: #FFFFFF;
                    border: 1.5px solid #E2E8F0;
                    border-radius: 14px;
                    padding: 12px 14px;
                    margin-bottom: 10px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
                ">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <div style="
                                width: 34px; height: 34px;
                                border-radius: 50%;
                                background: {'#FEE2E2' if is_admin else '#DCFCE7'};
                                border: 1.5px solid {'#F87171' if is_admin else '#86EFAC'};
                                display: flex; align-items: center; justify-content: center;
                                font-size: 16px;
                            ">{avatar}</div>
                            <div>
                                <div style="font-weight: 800; font-size: 13.5px; color: #0F172A; line-height: 1.2;">{user_name}</div>
                                <div style="font-size: 11px; color: {badge_color}; font-weight: 700;">{badge_text}</div>
                            </div>
                        </div>
                        <div style="
                            background: #FEF3C7;
                            color: #92400E;
                            border: 1px solid #FCD34D;
                            border-radius: 8px;
                            padding: 2px 7px;
                            font-size: 11.5px;
                            font-weight: 800;
                        ">🔥 {streak}d</div>
                    </div>
                    <!-- Mini XP Bar -->
                    <div style="display: flex; justify-content: space-between; font-size: 10.5px; color: #64748B; font-weight: 700; margin-bottom: 3px;">
                        <span>XP Progress</span>
                        <span>{xp} / {next_xp} XP</span>
                    </div>
                    <div style="width: 100%; height: 6px; background: #E2E8F0; border-radius: 9999px; overflow: hidden;">
                        <div style="width: {pct_bar}%; height: 100%; background: linear-gradient(90deg, #10B981, #166534); border-radius: 9999px;"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Quick Switch / Login link
            try:
                st.page_link("pages/0_Login.py", label="🔐 Switch Account / Login")
            except Exception:
                pass

            # 3. Family Shield Indicator if active
            if members_count > 0:
                st.markdown(
                    f"""
                    <div style="
                        background: #F0FDF4;
                        border: 1px solid #86EFAC;
                        border-radius: 10px;
                        padding: 7px 10px;
                        font-size: 11.5px;
                        color: #166534;
                        font-weight: 700;
                        display: flex; align-items: center; justify-content: space-between;
                        margin-bottom: 12px;
                    ">
                        <span>👨‍👩‍👧‍👦 Family Shield</span>
                        <span style="background: #DCFCE7; padding: 2px 6px; border-radius: 999px;">{members_count} Members</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        finally:
            db.close()

        # 4. Divider before Streamlit Nav Items
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 8px; margin: 10px 0 6px 0;">
                <span style="font-size: 10.5px; font-weight: 800; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.8px;">Navigation</span>
                <div style="flex-grow: 1; height: 1px; background: #E2E8F0;"></div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 5. Bottom Compliance Footer
        st.markdown(
            """
            <div style="
                margin-top: 24px;
                padding-top: 14px;
                border-top: 1px dashed #CBD5E1;
                font-size: 11px;
                color: #64748B;
                text-align: center;
                line-height: 1.4;
            ">
                <div style="font-weight: 700; color: #1E293B; margin-bottom: 2px;">⚡ Offline-First Architecture</div>
                <div>DPDP Act 2023 Compliant • FSSAI 2018</div>
            </div>
            """,
            unsafe_allow_html=True
        )

