"""
Vercel Serverless Entrypoint for FoodLens AI (FastAPI)
"""

import sys
import traceback
from pathlib import Path

# Ensure project root is in sys.path
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

try:
    from api.main import app
except Exception as e:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    err_msg = str(e)
    tb = traceback.format_exc()
    print(f"CRITICAL: Failed to import api.main: {err_msg}\n{tb}", flush=True)

    app = FastAPI(title="FoodLens AI - Startup Error Diagnostic")

    @app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE"])
    async def catch_all_error(path_name: str):
        return JSONResponse(
            status_code=500,
            content={
                "error": "STARTUP_IMPORT_FAILED",
                "message": err_msg,
                "traceback": tb.splitlines(),
            }
        )

# Expose app for Vercel ASGI runner
__all__ = ["app"]


