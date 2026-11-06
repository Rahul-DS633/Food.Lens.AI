"""
FoodLens AI — Vector Icon System
Provides clean, crisp SVG icons and badges (Lucide style) with zero external network dependency.
Replaces emoji-based iconography across all pages with modern, professional design.
"""

from typing import Optional


# High-precision SVG Path definitions (24x24 viewBox, stroke-width 2, linecap/linejoin round)
_SVG_ICONS = {
    # Navigation & Core Tools
    "camera": '<path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/>',
    "barcode": '<path d="M3 5v14"/><path d="M8 5v14"/><path d="M12 5v14"/><path d="M17 5v14"/><path d="M21 5v14"/><path d="M6 7v10"/><path d="M15 7v10"/>',
    "scale": '<path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="M7 21h10"/><path d="M12 3v18"/><path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/>',
    "gamepad": '<line x1="6" x2="10" y1="12" y2="12"/><line x1="8" x2="8" y1="10" y2="14"/><line x1="15" x2="15.01" y1="13" y2="13"/><line x1="18" x2="18.01" y1="11" y2="11"/><rect width="20" height="12" x="2" y="6" rx="6"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "history": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "settings": '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',

    # Nutrients & Biomarkers
    "energy": '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    "bolt": '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    "protein": '<path d="m6.5 6.5 11 11"/><path d="m21 21-1-1"/><path d="m3 3 1 1"/><path d="m18 22 4-4"/><path d="m2 6 4-4"/><path d="m3 10 7-7"/><path d="m14 21 7-7"/>',
    "carbs": '<path d="m2 22 10-10"/><path d="M16 8a4 4 0 0 0-4-4 4 4 0 0 0-4 4c0 2.2 1.8 4 4 4a4 4 0 0 0 4-4Z"/><path d="M19 13a4 4 0 0 0-4-4 4 4 0 0 0-4 4c0 2.2 1.8 4 4 4a4 4 0 0 0 4-4Z"/><path d="M13 19a4 4 0 0 0-4-4 4 4 0 0 0-4 4c0 2.2 1.8 4 4 4a4 4 0 0 0 4-4Z"/>',
    "wheat": '<path d="m2 22 10-10"/><path d="M16 8a4 4 0 0 0-4-4 4 4 0 0 0-4 4c0 2.2 1.8 4 4 4a4 4 0 0 0 4-4Z"/><path d="M19 13a4 4 0 0 0-4-4 4 4 0 0 0-4 4c0 2.2 1.8 4 4 4a4 4 0 0 0 4-4Z"/><path d="M13 19a4 4 0 0 0-4-4 4 4 0 0 0-4 4c0 2.2 1.8 4 4 4a4 4 0 0 0 4-4Z"/>',
    "sugar": '<path d="m21 16-9 5-9-5V8l9-5 9 5v8Z"/><path d="m3.3 7.3 8.7 5 8.7-5"/><path d="M12 12.3V21"/>',
    "cubes": '<path d="m21 16-9 5-9-5V8l9-5 9 5v8Z"/><path d="m3.3 7.3 8.7 5 8.7-5"/><path d="M12 12.3V21"/>',
    "fat": '<path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"/>',
    "droplet": '<path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"/>',
    "sat_fat": '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
    "layers": '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
    "fibre": '<path d="M7 20h10"/><path d="M10 20c5.5-2.5.8-6.4 3-10"/><path d="M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4-.1 5.5.8z"/><path d="M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z"/>',
    "sprout": '<path d="M7 20h10"/><path d="M10 20c5.5-2.5.8-6.4 3-10"/><path d="M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4-.1 5.5.8z"/><path d="M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z"/>',
    "sodium": '<path d="M12 2v20"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
    "salt": '<path d="M12 2v20"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',

    # Gamification & Status
    "flame": '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>',
    "fire": '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>',
    "shield": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>',
    "trophy": '<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/>',
    "medal": '<path d="m15.477 12.89 1.515 8.526a.5.5 0 0 1-.722.522L12 19.808l-4.27 2.13a.5.5 0 0 1-.722-.522l1.515-8.526"/><circle cx="12" cy="8" r="6"/>',
    "award": '<circle cx="12" cy="8" r="6"/><path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/>',
    "crown": '<path d="m2 4 3 12h14l3-12-6 7-4-7-4 7-6-7zm3 16h14"/>',
    "book": '<path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/><path d="M6 6h10"/><path d="M6 10h10"/>',

    # UI Helpers & Indicators
    "sparkles": '<path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3L12 3z"/><path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/>',
    "check": '<polyline points="20 6 9 17 4 12"/>',
    "check_circle": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
    "alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "leaf": '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>',
    "utensils": '<path d="M18 2v6a3 3 0 0 1-3 3 3 3 0 0 1-3-3V2"/><path d="M14 2v20"/><path d="M6 2v10a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2V2"/><path d="M9 14v8"/>',
    "eye": '<path d="2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>',
    "upload": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>',
    "trash": '<polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
}


def get_icon_svg(
    name: str,
    size: int = 20,
    color: Optional[str] = None,
    stroke_width: float = 2.0,
    filled: bool = False,
    extra_style: str = ""
) -> str:
    """
    Returns an inline SVG string for the requested icon name.
    """
    key = name.lower().strip()
    path_data = _SVG_ICONS.get(key)
    if not path_data:
        # Fallback to info circle
        path_data = _SVG_ICONS["info"]

    color_attr = color or "currentColor"
    fill_attr = color_attr if filled else "none"

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="{fill_attr}" stroke="{color_attr}" stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round" '
        f'style="display: inline-block; vertical-align: middle; flex-shrink: 0; {extra_style}">'
        f'{path_data}'
        f'</svg>'
    )


def icon_badge(
    name: str,
    bg: str = "#F0FDF4",
    color: str = "#1B5E3F",
    size: int = 20,
    badge_size: int = 40,
    border: Optional[str] = None
) -> str:
    """
    Returns an icon encapsulated in a stylish rounded pill or circular container.
    """
    border_style = f"border: 1px solid {border};" if border else ""
    svg = get_icon_svg(name, size=size, color=color)
    return (
        f'<div style="width: {badge_size}px; height: {badge_size}px; border-radius: 12px; '
        f'background: {bg}; {border_style} display: inline-flex; align-items: center; '
        f'justify-content: center; box-shadow: 0 2px 6px rgba(0,0,0,0.04);">'
        f'{svg}'
        f'</div>'
    )

