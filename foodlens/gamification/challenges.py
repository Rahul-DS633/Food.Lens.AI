"""
FoodLens Quest Daily Challenges & Mini-Games
1. Guess Before You Scan
2. Serving Trap Quiz
3. Daily Literacy Quests
"""

from datetime import date
from typing import Dict, Any, Tuple


DAILY_QUEST_ROTATION = [
    {
        "id": "dq_sugar_under_5",
        "title": "Sugar Detective",
        "description": "Find a packaged food with less than 5g of sugar per 100g.",
        "xp_reward": 20,
    },
    {
        "id": "dq_multi_serving",
        "title": "Serving Trap Hunter",
        "description": "Scan a single packet that contains more than 2 servings.",
        "xp_reward": 25,
    },
    {
        "id": "dq_compare_snacks",
        "title": "Smart Switch",
        "description": "Compare two packaged snacks side-by-side.",
        "xp_reward": 20,
    },
    {
        "id": "dq_verify_label",
        "title": "Label Verifier",
        "description": "Scan an OCR label and confirm the extracted values.",
        "xp_reward": 20,
    },
]


def get_daily_challenge(today: date) -> Dict[str, Any]:
    """Rotates daily quests based on day of year."""
    index = today.timetuple().tm_yday % len(DAILY_QUEST_ROTATION)
    quest = dict(DAILY_QUEST_ROTATION[index])
    quest["date"] = today.isoformat()
    return quest


def evaluate_sugar_guess(actual_sugar_g: float, guessed_sugar_g: float) -> Tuple[int, str]:
    """
    Mini-Game 1: Guess Before You Scan
    Evaluates closeness between user guess and true label sugar.
    """
    error = abs(actual_sugar_g - guessed_sugar_g)
    if error <= 1.5:
        return 25, f"🎯 Bullseye! You guessed {guessed_sugar_g}g and actual was {actual_sugar_g}g! (+25 XP)"
    elif error <= 4.0:
        return 15, f"👏 Great estimation! You guessed {guessed_sugar_g}g, actual was {actual_sugar_g}g. (+15 XP)"
    else:
        return 10, f"💡 Good try! You guessed {guessed_sugar_g}g, but the label reveals {actual_sugar_g}g! (+10 XP)"


def evaluate_serving_trap_answer(actual_servings: float, chosen_servings: float) -> Tuple[int, str]:
    """
    Mini-Game 2: Serving Trap Quiz
    Tests user awareness of single packet containing multiple servings.
    """
    error = abs(actual_servings - chosen_servings)
    if error <= 0.2:
        return 20, f"🎉 Correct! The packet actually contains {actual_servings:.1f} servings! (+20 XP)"
    else:
        return 10, f"👀 Tricky packet! It actually holds {actual_servings:.1f} servings, not {chosen_servings}! (+10 XP)"
