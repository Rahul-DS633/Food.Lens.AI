"""
FoodLens API Dependencies
"""

from typing import Generator
from sqlalchemy.orm import Session
from db.session import SessionLocal, get_db

__all__ = ["get_db", "SessionLocal"]
