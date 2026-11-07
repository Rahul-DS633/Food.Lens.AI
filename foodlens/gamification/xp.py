"""
FoodLens Quest XP & Leveling Engine
Rules:
1. Reward literacy and verification actions: scanning (+10), verifying/correcting (+15),
   new product (+20), comparing (+15), mini-games (+10 to +25).
2. Never reward restriction, low calories, or eating choices.
3. Daily XP cap (150 XP) and per-product cap (45 XP) to prevent spam.
4. Level progression:
   - 0-99 XP: Label Rookie
   - 100-249 XP: Label Reader
   - 250-499 XP: Label Detective
   - 500-999 XP: Nutrition Navigator
   - 1000+ XP: Food Intelligence Pro
"""

from typing import Tuple

DAILY_XP_CAP = 150
PRODUCT_XP_CAP = 45

LEVEL_THRESHOLDS = [
    (1000, "Food Intelligence Pro", "🏆"),
    (500, "Nutrition Navigator", "🧭"),
    (250, "Label Detective", "🔍"),
    (100, "Label Reader", "📖"),
    (0, "Label Rookie", "🌱"),
]

ACTION_XP_VALUES = {
    "scan": 10,
    "correction": 15,
    "new_product": 20,
    "compare": 15,
    "minigame_easy": 10,
    "minigame_perfect": 25,
}


def get_level_for_xp(xp: int) -> Tuple[str, str, int, int]:
    """
    Returns (level_name, level_icon, current_level_base, next_level_xp).
    """
    if xp >= 1000:
        return "Food Intelligence Pro", "🏆", 1000, 2000
    if xp >= 500:
        return "Nutrition Navigator", "🧭", 500, 1000
    if xp >= 250:
        return "Label Detective", "🔍", 250, 500
    if xp >= 100:
        return "Label Reader", "📖", 100, 250
    return "Label Rookie", "🌱", 0, 100


def calculate_xp_award(
    action: str,
    current_daily_xp: int = 0,
    current_product_xp: int = 0,
    custom_xp: int = 0
) -> int:
    """
    Calculates actual XP awarded respecting daily and per-product safety caps.
    """
    base_xp = custom_xp if custom_xp > 0 else ACTION_XP_VALUES.get(action, 10)

    # Apply daily cap
    available_daily = max(0, DAILY_XP_CAP - current_daily_xp)
    # Apply product cap if applicable
    available_product = max(0, PRODUCT_XP_CAP - current_product_xp) if current_product_xp > 0 else base_xp

    awarded = min(base_xp, available_daily, available_product)
    return awarded

