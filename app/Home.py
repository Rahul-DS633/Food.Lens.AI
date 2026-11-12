"""
FoodLens AI — Home & Quick Scanner Hub
Features interactive 3D WebGL Three.js hero, vector icon system,
and realistic packaged food visual showcase.
"""

import sys
import os
from pathlib import Path

# Load environment variables from .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Ensure project root is on sys.path so 'db' and 'foodlens' packages resolve
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st

# Propagate Streamlit Cloud secrets to environment variables if present
try:
    if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
        os.environ["GEMINI_API_KEY"] = str(st.secrets["GEMINI_API_KEY"])
except Exception:
    pass
from datetime import date

# Setup page configuration
st.set_page_config(
    page_title="FoodLens AI — Food Intelligence",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load theme CSS
CSS_PATH = Path(__file__).parent / "assets" / "theme.css"
if CSS_PATH.exists():
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.html(f"<style>{f.read()}</style>")

from db.session import SessionLocal, init_db, engine
from db.models import Base, User, Product
from foodlens.gamification.xp import get_level_for_xp
from foodlens.gamification.challenges import get_daily_challenge
from app.components.xp_bar import render_xp_header
from app.components.icons import get_icon_svg, icon_badge
from app.components.images import get_product_image
from app.components.three_d import render_3d_hero
from app.components.sidebar import render_sidebar

# Ensure database tables and seeds exist before rendering
try:
    Base.metadata.create_all(bind=engine)
    init_db()
except Exception as _e:
    pass

# Initialize session state variables
if "user_id" not in st.session_state:
    st.session_state.user_id = 1
if "language" not in st.session_state:
    st.session_state.language = "en"
if "current_scan_product_id" not in st.session_state:
    st.session_state.current_scan_product_id = None
if "active_scan_tab" not in st.session_state:
    st.session_state.active_scan_tab = "camera"

# Render custom sidebar
render_sidebar("Home")

# Display feedback toast if coming from Profile save
if st.session_state.get("profile_saved_toast"):
    st.toast("🎉 Dietary profile saved! Personalized Food Fit is now active for all scans.", icon="🛡️")
    st.session_state["profile_saved_toast"] = False

# Fetch user progress from DB
db = SessionLocal()
try:
    user = None
    try:
        user = db.query(User).filter(User.id == st.session_state.user_id).first()
    except Exception:
        try:
            init_db()
            user = db.query(User).filter(User.id == st.session_state.user_id).first()
        except Exception:
            user = None

    progress = user.progress if user else None
    xp = progress.xp if progress else 25
    level = progress.level if progress else "Label Rookie"
    streak = progress.current_streak if progress else 1
    freezes = progress.streak_freezes if progress else 1

    lvl_name, lvl_icon, base_xp, next_xp = get_level_for_xp(xp)

    # 1. Render Header XP & Streak Bar
    render_xp_header(
        xp=xp,
        level=lvl_name,
        level_icon=lvl_icon,
        base_xp=base_xp,
        next_xp=next_xp,
        current_streak=streak,
        streak_freezes=freezes
    )

    # 2. Interactive Three.js 3D WebGL Hero Canvas
    render_3d_hero(height=230)

    # 3. Hero Title & Language Switcher
    HOME_TRANSLATIONS = {
        "en": {
            "intelligence_pill": "Grounded Food Intelligence",
            "hero_title": "FoodLens AI",
            "hero_subtitle": "Point your camera at any packaged food and discover what is <i>really</i> inside — with 100% deterministic arithmetic and every single number traceable to its label source.",
            "daily_quest": "DAILY QUEST",
            "literacy_reward": "Literacy Reward",
            "card_scan_title": "Scan a Food",
            "card_scan_desc": "Multi-angle camera capture, photo uploads & OCR label verification with INS ingredient mapping.",
            "btn_scan": "Open Scanner →",
            "card_compare_title": "Compare Foods",
            "card_compare_desc": "Side-by-side per-100g nutritional evaluation to spot hidden sugars, saturated fats, and sodium.",
            "btn_compare": "Compare Snacks →",
            "card_quest_title": "FoodLens Quest",
            "card_quest_desc": "Guess Before You Scan mini-game, Serving Trap quiz, streak protection, and milestone badges.",
            "btn_quest": "Play Mini-Games →",
            "showcase_title": "Verified Indian Products (Instant 1-Click Inspection)",
            "showcase_subtitle": "Select any popular packaged item below to view authentic packaging photography, live portion calculation, 3D sugar cubes, and grounded AI analysis:",
            "btn_inspect": "Inspect",
            "sugar_suffix": "sugar",
        },
        "hi": {
            "intelligence_pill": "सटीक खाद्य विश्लेषण (Food Intelligence)",
            "hero_title": "फूडलेंस एआई (FoodLens AI)",
            "hero_subtitle": "किसी भी पैकेज्ड फूड पर अपना कैमरा घुमाएं और जानें कि उसके अंदर <i>वास्तव में</i> क्या है — 100% सटीक गणित और लेबल से सत्यापित हर संख्या के साथ।",
            "daily_quest": "दैनिक क्व्वेस्ट (DAILY QUEST)",
            "literacy_reward": "साक्षरता पुरस्कार",
            "card_scan_title": "भोजन स्कैन करें",
            "card_scan_desc": "मल्टी-एंगल कैमरा, फोटो अपलोड और आईएनएस (INS) सामग्री विश्लेषण के साथ ओसीआर सत्यापन।",
            "btn_scan": "स्कैनर खोलें →",
            "card_compare_title": "तुलना करें",
            "card_compare_desc": "छिपी हुई चीनी, संतृप्त वसा और सोडियम की पहचान के लिए प्रति 100 ग्राम तुलना।",
            "btn_compare": "स्नैक्स की तुलना करें →",
            "card_quest_title": "फूडलेंस क्व्वेस्ट",
            "card_quest_desc": "स्कैन करने से पहले अनुमान लगाएं, सर्विंग ट्रैप क्विज, दैनिक स्ट्रीक और बैज जीतें।",
            "btn_quest": "मिनी-गेम्स खेलें →",
            "showcase_title": "सत्यापित भारतीय उत्पाद (1-क्लिक निरीक्षण)",
            "showcase_subtitle": "असली पैकेजिंग फोटो, सर्विंग कैलकुलेटर, 3D चीनी के क्यूब्स और एआई विश्लेषण देखने के लिए नीचे दिए गए किसी भी उत्पाद को चुनें:",
            "btn_inspect": "जांचें",
            "sugar_suffix": "चीनी",
        }
    }

    col_t1, col_t2 = st.columns([3, 1])
    with col_t2:
        current_lang = st.session_state.get("language", "en")
        selected_lang_label = st.radio(
            "Language / भाषा",
            ["English", "हिंदी"],
            index=1 if current_lang == "hi" else 0,
            horizontal=True,
            key="home_language_toggle",
            label_visibility="collapsed"
        )
        new_lang = "hi" if selected_lang_label == "हिंदी" else "en"
        if new_lang != current_lang:
            st.session_state.language = new_lang
            st.rerun()

    active_lang = st.session_state.get("language", "en")
    t = HOME_TRANSLATIONS.get(active_lang, HOME_TRANSLATIONS["en"])

    with col_t1:
        sparkle_icon = get_icon_svg("sparkles", size=18, color="#1B5E3F")
        hero_html = (
            f'<div style="display: flex; align-items: center; gap: 8px; margin-top: 10px;">'
            f'<span class="pill-badge pill-xp" style="margin-bottom: 2px;">{sparkle_icon} {t["intelligence_pill"]}</span>'
            f'</div>'
            f'<h1 style="color: #144730; margin: 4px 0 6px 0; font-size: 32px;">{t["hero_title"]}</h1>'
            f'<p style="font-size: 15.5px; color: #475569; line-height: 1.5; margin-bottom: 16px;">{t["hero_subtitle"]}</p>'
        )
        if hasattr(st, "html"):
            st.html(hero_html)
        else:
            st.markdown(hero_html, unsafe_allow_html=True)

    # 4. Today's Quest Card
    today_quest = get_daily_challenge(date.today())
    trophy_icon = get_icon_svg("trophy", size=22, color="#166534")
    quest_title = today_quest["title"]
    quest_desc = today_quest["description"]
    if active_lang == "hi":
        quest_title = today_quest.get("title_hi", today_quest["title"])
        quest_desc = today_quest.get("description_hi", today_quest["description"])

    quest_card_html = (
        f'<div class="foodlens-card-3d" style="background: linear-gradient(90deg, #F0FDF4 0%, #ECFCCB 100%); border: 1.5px solid #86EFAC; margin-bottom: 22px;">'
        f'<div style="display: flex; justify-content: space-between; align-items: center;">'
        f'<div style="display: flex; align-items: center; gap: 14px;">'
        f'<div style="width: 46px; height: 46px; border-radius: 12px; background: rgba(255,255,255,0.8); display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">{trophy_icon}</div>'
        f'<div>'
        f'<span style="background: #1B5E3F; color: #FFFFFF !important; font-size: 11px; font-weight: 800; padding: 3px 8px; border-radius: 6px; letter-spacing: 0.5px;">{t["daily_quest"]}</span>'
        f'<h3 style="margin: 4px 0 2px 0; color: #166534; font-size: 17px;">{quest_title}</h3>'
        f'<div style="color: #374151; font-size: 13.5px;">{quest_desc}</div>'
        f'</div>'
        f'</div>'
        f'<div style="text-align: right;">'
        f'<div style="font-size: 22px; font-weight: 800; color: #1B5E3F; font-family: \'JetBrains Mono\', monospace;">+{today_quest["xp_reward"]} XP</div>'
        f'<span style="font-size: 12px; font-weight: 600; color: #475569;">{t["literacy_reward"]}</span>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    if hasattr(st, "html"):
        st.html(quest_card_html)
    else:
        st.markdown(quest_card_html, unsafe_allow_html=True)

    # 5. Quick Action Columns (3D Elevating Cards with Vector Badges)
    col1, col2, col3 = st.columns(3)

    cam_badge = icon_badge("camera", bg="#DCFCE7", color="#166534", size=24, badge_size=48)
    scale_badge = icon_badge("scale", bg="#EFF6FF", color="#2563EB", size=24, badge_size=48)
    game_badge = icon_badge("gamepad", bg="#FDF4FF", color="#9333EA", size=24, badge_size=48)

    with col1:
        card1_html = (
            f'<div class="action-card-3d">'
            f'<div style="margin-bottom: 12px;">{cam_badge}</div>'
            f'<h3 style="color: #144730; margin: 0 0 6px 0; font-size: 18px;">{t["card_scan_title"]}</h3>'
            f'<p style="font-size: 13.5px; color: #475569; min-height: 42px; line-height: 1.4;">{t["card_scan_desc"]}</p>'
            f'</div>'
        )
        if hasattr(st, "html"):
            st.html(card1_html)
        else:
            st.markdown(card1_html, unsafe_allow_html=True)
        if st.button(t["btn_scan"], width="stretch", type="primary", key="btn_scan_home"):
            st.switch_page("pages/1_Scan.py")

    with col2:
        card2_html = (
            f'<div class="action-card-3d">'
            f'<div style="margin-bottom: 12px;">{scale_badge}</div>'
            f'<h3 style="color: #144730; margin: 0 0 6px 0; font-size: 18px;">{t["card_compare_title"]}</h3>'
            f'<p style="font-size: 13.5px; color: #475569; min-height: 42px; line-height: 1.4;">{t["card_compare_desc"]}</p>'
            f'</div>'
        )
        if hasattr(st, "html"):
            st.html(card2_html)
        else:
            st.markdown(card2_html, unsafe_allow_html=True)
        if st.button(t["btn_compare"], width="stretch", key="btn_comp_home"):
            st.switch_page("pages/3_Compare.py")

    with col3:
        card3_html = (
            f'<div class="action-card-3d">'
            f'<div style="margin-bottom: 12px;">{game_badge}</div>'
            f'<h3 style="color: #144730; margin: 0 0 6px 0; font-size: 18px;">{t["card_quest_title"]}</h3>'
            f'<p style="font-size: 13.5px; color: #475569; min-height: 42px; line-height: 1.4;">{t["card_quest_desc"]}</p>'
            f'</div>'
        )
        if hasattr(st, "html"):
            st.html(card3_html)
        else:
            st.markdown(card3_html, unsafe_allow_html=True)
        if st.button(t["btn_quest"], width="stretch", key="btn_quest_home"):
            st.switch_page("pages/4_Quest.py")

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # 6. Realistic Packaged Food Visual Showcase (Instant Demos)
    bolt_icon = get_icon_svg("bolt", size=22, color="#EA580C")
    showcase_html = (
        f'<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">'
        f'{bolt_icon}<h2 style="color: #144730; margin: 0; font-size: 22px;">{t["showcase_title"]}</h2>'
        f'</div>'
        f'<p style="color: #64748B; font-size: 14px; margin-bottom: 16px;">{t["showcase_subtitle"]}</p>'
    )
    if hasattr(st, "html"):
        st.html(showcase_html)
    else:
        st.markdown(showcase_html, unsafe_allow_html=True)

    preseeded_prods = db.query(Product).limit(5).all()
    demo_cols = st.columns(len(preseeded_prods))

    for idx, p in enumerate(preseeded_prods):
        img_uri = get_product_image(p.name, p.brand, p.category, p.image_url)
        n = p.nutrition
        cals = f"{n.energy_kcal:g} kcal" if (n and n.energy_kcal) else "N/A"
        sugars = f"{n.sugars_g:g}g {t['sugar_suffix']}" if (n and n.sugars_g is not None) else ""

        with demo_cols[idx]:
            card_p_html = (
                f'<div class="product-card-3d" style="padding: 12px; text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: space-between;">'
                f'<div>'
                f'<div style="width: 100%; height: 130px; border-radius: 12px; overflow: hidden; background: #FFFFFF; margin-bottom: 10px; border: 1.5px solid #E2E8F0; display: flex; align-items: center; justify-content: center; padding: 6px; box-shadow: inset 0 1px 3px rgba(0,0,0,0.02);">'
                f'<img src="{img_uri}" alt="{p.name}" style="max-width: 100%; max-height: 100%; object-fit: contain; transition: transform 0.3s ease;">'
                f'</div>'
                f'<div style="display: flex; justify-content: center; gap: 4px; margin-bottom: 6px;">'
                f'<span style="font-size: 10.5px; font-weight: 700; padding: 2px 7px; border-radius: 6px; background: #DCFCE7; color: #166534; text-transform: uppercase;">{p.brand}</span>'
                f'<span style="font-size: 10.5px; font-weight: 600; padding: 2px 6px; border-radius: 6px; background: #F1F5F9; color: #475569;">{p.category}</span>'
                f'</div>'
                f'<div style="font-weight: 800; font-size: 13.5px; color: #0F172A; line-height: 1.3; min-height: 36px; margin-bottom: 8px;">{p.name}</div>'
                f'<div style="font-size: 11.5px; color: #64748B; margin-bottom: 10px;"><b style="color: #0F172A;">{cals}</b> {f"• {sugars}" if sugars else ""}</div>'
                f'</div>'
                f'</div>'
            )
            if hasattr(st, "html"):
                st.html(card_p_html)
            else:
                st.markdown(card_p_html, unsafe_allow_html=True)

            if st.button(f"{t['btn_inspect']} {p.brand}", key=f"demo_btn_{p.id}", width="stretch"):
                st.session_state.current_scan_product_id = p.id
                st.switch_page("pages/2_Result.py")

finally:
    db.close()
