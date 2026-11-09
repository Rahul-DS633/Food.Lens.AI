"""
FoodLens AI - FastAPI Application
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from foodlens.web_ui import get_foodlens_html_portal
from api.routes import (
    scan, nutrition, products, compare, advice, quest, history, profile, personal_fit, sugar, reports, admin, household, claims
)
from db.session import init_db

# Initialize database schema on startup safely
try:
    init_db()
except Exception as _e:
    print(f"Warning: Database initialization during startup: {_e}", flush=True)

app = FastAPI(
    title="FoodLens AI API",
    description="Packaged-food intelligence API: deterministic nutrition engine, OCR extraction, transparent scoring, and FoodLens Quest.",
    version="1.0.0",
)

# CORS middleware for Web / Streamlit / Mobile clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register Routers
app.include_router(scan.router)
app.include_router(nutrition.router)
app.include_router(products.router)
app.include_router(compare.router)
app.include_router(advice.router)
app.include_router(quest.router)
app.include_router(history.router)
app.include_router(profile.router)
app.include_router(personal_fit.router)
app.include_router(sugar.router)
app.include_router(reports.router)
app.include_router(admin.router)
app.include_router(household.router)
app.include_router(claims.router)


@app.get("/", response_class=HTMLResponse)
@app.get("/api/index.py", response_class=HTMLResponse)
@app.get("/api/index", response_class=HTMLResponse)
def root(request: Request):
    accept = request.headers.get("accept", "")
    if "application/json" in accept and "text/html" not in accept:
        return JSONResponse(content={
            "app": "FoodLens AI",
            "version": "1.0.0",
            "status": "operational",
            "docs_url": "/docs",
            "principles": [
                "Deterministic code calculates",
                "Never invent or zero-fill missing values",
                "Every value carries provenance",
                "Neutral language",
                "User always can correct extraction"
            ]
        })
    return HTMLResponse(content=get_foodlens_html_portal())


@app.get("/api", response_class=JSONResponse)
@app.get("/api/status", response_class=JSONResponse)
def api_status():
    return {
        "app": "FoodLens AI",
        "version": "1.0.0",
        "status": "operational",
        "docs_url": "/docs",
        "principles": [
            "Deterministic code calculates",
            "Never invent or zero-fill missing values",
            "Every value carries provenance",
            "Neutral language",
            "User always can correct extraction"
        ]
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
