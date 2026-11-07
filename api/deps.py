"""
FoodLens API Dependencies
"""

from db.session import SessionLocal, get_db

__all__ = ["get_db", "SessionLocal"]
