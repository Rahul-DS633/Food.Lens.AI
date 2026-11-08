"""
Vercel Serverless Entrypoint for FoodLens AI (FastAPI)
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from api.main import app

# Expose app for Vercel ASGI runner
__all__ = ["app"]

