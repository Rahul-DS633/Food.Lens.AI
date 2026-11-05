"""
FoodLens AI - FastAPI Application
"""

import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import scan, nutrition, products, compare, advice, quest, history
from db.session import init_db

# Initialize database schema on startup
init_db()

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


@app.get("/")
def root():
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
