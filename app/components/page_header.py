"""
FoodLens AI — Unified Emerald Page Header Component
Renders an ultra-premium deep emerald gradient banner with subtle border,
translucent icon container with vibrant emoji iconography, energetic lime overline,
crisp white typography, and contextual status badges matching the FoodLens design language.
"""

from typing import List, Optional, Dict, Any
import streamlit as st
from app.components.icons import get_icon_svg

_EMOJI_LOOKUP = {
    "camera": "📷",
    "search": "🔍",
    "scale": "⚖️",
    "trophy": "🏆",
    "history": "📜",
    "settings": "⚙️",
    "shield": "🛡️",
    "users": "👨‍👩‍👧‍👦",
    "user": "👤",
    "lock": "🔐",
    "sparkles": "✨",
    "barcode": "🏷️",
    "bolt": "⚡",
    "flame": "🔥",
    "leaf": "🥗",
    "check_circle": "✓",
    "target": "🎯",
    "alert": "🚨",
    "book": "📖",
}


def render_page_header(
    title: str,
    subtitle: Optional[str] = None,
    icon_name: str = "sparkles",
    emoji: Optional[str] = None,
    overline: Optional[str] = None,
    action_pills: Optional[List[Dict[str, str]]] = None,
) -> None:
    """
    Renders an ultra-premium emerald hero banner matching the FoodLens design language.
    Features a translucent glass square holding a colorful emoji or vector icon.
    """
    # 1. Resolve main icon / emoji
    main_emoji = emoji or _EMOJI_LOOKUP.get(icon_name.lower().strip())
    if main_emoji:
        display_icon = (
            f'<span style="font-size: 26px; line-height: 1; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.25)); '
            f'display: inline-block;">{main_emoji}</span>'
        )
    else:
        display_icon = get_icon_svg(icon_name, size=24, color="#A3E635")

    # 2. Resolve contextual action pills with emoji or icon
    pills_html = []
    if action_pills:
        for pill in action_pills:
            p_icon = pill.get("icon", "")
            p_text = pill.get("text", "")
            p_emoji = pill.get("emoji") or _EMOJI_LOOKUP.get(p_icon.lower().strip(), "")
            if p_emoji:
                p_badge = f'<span style="font-size: 14px; line-height: 1;">{p_emoji}</span>'
            elif p_icon:
                p_badge = get_icon_svg(p_icon, size=14, color="#A3E635")
            else:
                p_badge = ""

            pills_html.append(
                f'<div style="background: rgba(0, 0, 0, 0.22); border: 1px solid rgba(255, 255, 255, 0.18); '
                f'border-radius: 12px; padding: 7px 14px; display: inline-flex; align-items: center; gap: 7px; '
                f'color: #FFFFFF; font-size: 12.5px; font-weight: 700; box-shadow: 0 2px 6px rgba(0,0,0,0.12); '
                f'white-space: nowrap;">'
                f'{p_badge}<span>{p_text}</span>'
                f'</div>'
            )
    pills_container_html = (
        f'<div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-top: 4px;">'
        f'{"".join(pills_html)}'
        f'</div>'
        if pills_html else ""
    )

    overline_html = (
        f'<div style="font-size: 11px; text-transform: uppercase; font-weight: 800; letter-spacing: 0.9px; '
        f'color: #A3E635 !important; margin-bottom: 2px;">{overline}</div>'
        if overline else ""
    )

    subtitle_html = (
        f'<div style="font-size: 13.5px; color: rgba(255, 255, 255, 0.88) !important; margin-top: 4px; '
        f'line-height: 1.45; max-width: 820px;">{subtitle}</div>'
        if subtitle else ""
    )

    banner_html = (
        f'<div class="foodlens-page-banner" style="'
        f'background: linear-gradient(135deg, #144730 0%, #1B5E3F 60%, #2E7D56 100%); '
        f'border: 1px solid rgba(255, 255, 255, 0.18); '
        f'border-radius: 18px; '
        f'padding: 18px 24px; '
        f'color: #FFFFFF !important; '
        f'margin-bottom: 22px; '
        f'box-shadow: 0 10px 25px -5px rgba(20, 71, 48, 0.35), inset 0 1px 1px rgba(255, 255, 255, 0.2); '
        f'display: flex; '
        f'justify-content: space-between; '
        f'align-items: center; '
        f'flex-wrap: wrap; '
        f'gap: 16px;">'
        f'<div style="display: flex; align-items: center; gap: 14px; flex-grow: 1;">'
        f'<div style="width: 48px; height: 48px; min-width: 48px; border-radius: 13px; '
        f'background: rgba(255, 255, 255, 0.14); border: 1.5px solid rgba(255, 255, 255, 0.28); '
        f'display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(0,0,0,0.18);">'
        f'{display_icon}'
        f'</div>'
        f'<div>'
        f'{overline_html}'
        f'<h1 style="font-size: 22px; font-weight: 800; color: #FFFFFF !important; letter-spacing: -0.3px; '
        f'margin: 0; line-height: 1.2;">{title}</h1>'
        f'{subtitle_html}'
        f'</div>'
        f'</div>'
        f'{pills_container_html}'
        f'</div>'
    )

    if hasattr(st, "html"):
        st.html(banner_html)
    else:
        st.markdown(banner_html, unsafe_allow_html=True)
