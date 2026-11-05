"""
FoodLens Quest Streak Engine
Tracks daily activity streaks with gentle wording and protective streak freezes.
"""

from datetime import date, timedelta
from typing import Tuple


def update_user_streak(
    last_active_date_str: str,
    current_streak: int,
    longest_streak: int,
    streak_freezes: int,
    today: date
) -> Tuple[int, int, int, str]:
    """
    Updates user streak based on activity date.
    Returns: (new_current_streak, new_longest_streak, new_streak_freezes, feedback_message)
    """
    today_str = today.isoformat()

    if not last_active_date_str:
        # First active day
        return 1, max(longest_streak, 1), streak_freezes, "Welcome to FoodLens Quest! Day 1 streak started!"

    if last_active_date_str == today_str:
        # Already logged in today
        return current_streak, longest_streak, streak_freezes, "Activity logged for today! Streak active."

    try:
        last_date = date.fromisoformat(last_active_date_str)
    except ValueError:
        return 1, max(longest_streak, 1), streak_freezes, "Streak restarted!"

    days_diff = (today - last_date).days

    if days_diff == 1:
        # Consecutive day!
        new_streak = current_streak + 1
        new_longest = max(longest_streak, new_streak)
        return new_streak, new_longest, streak_freezes, f"🔥 Streak alive! {new_streak} days in a row!"

    elif days_diff == 2 and streak_freezes > 0:
        # Missed yesterday, but saved by streak freeze
        new_freezes = streak_freezes - 1
        new_streak = current_streak + 1
        new_longest = max(longest_streak, new_streak)
        return (
            new_streak,
            new_longest,
            new_freezes,
            f"🛡️ Streak Freeze used! Your {new_streak}-day streak was protected without penalty."
        )

    else:
        # Streak reset gently
        return 1, longest_streak, streak_freezes, "Welcome back! Ready to explore today's food intelligence."
