"""
FoodLens AI - Root ASGI Entrypoint for Vercel and Production
"""
import sys
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from api.main import app

__all__ = ["app"]

