# FoodLens AI 🔍🥗

> **Point your camera at any packaged food and discover what is really inside, how much you are actually eating, and how it compares — with every number traceable to its source.**

[![CI](https://github.com/foodlens-ai/foodlens-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/foodlens-ai/foodlens-ai)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.38+-FF4B4B.svg)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/tests-106%20passed-brightgreen.svg)](tests/)

---

## 🌟 Key Differentiators
- 🇮🇳 **Indian Packaged-Food Focus:** Built-in EAN-13 India (890) validation and pre-seeded database of common Indian staples (Parle-G, Maggi, Haldiram's Bhujia, Amul Butter, Frooti).
- ⚙️ **Deterministic Calculation:** Zero LLM hallucinations on math. All scaling, unit conversions (kJ↔kcal, salt↔sodium), and energy cross-checks run via pure Python.
- 👨‍👩‍👧‍👦 **Family Dietary Profiles:** Multi-person allergen shields & interactive matrix for up to 8 household members with DPDP Act (2023) minor consent safeguards.
- 🔊 **Hindi & English Read-Aloud:** Deterministic spoken audio narration (<45s) with browser SpeechSynthesis and phonetic units (grams/ग्राम, calories/किलोकैलोरी, tsp/चम्मच).
- 🚩 **Report Wrong Data & Admin Review Queue:** Community-driven accuracy reporting with EXIF stripping, auto-checks, consensus priority, and immutable audit revisions (`product_revisions`).
- 🔬 **Hidden Sugar & Sweetener Detector:** Categorizes sugars, syrups, concentrates, carb fillers, and non-sugar sweeteners. Detects 'sugar splitting' and nutrition table conflicts.
- 🛡️ **Personalized Food Fit & Allergens:** Demographic-aware guidance (ICMR-NIN 2020 RDA) and deterministic allergen alerts with India DPDP Act 2023 compliance.
- 🧊 **Sugar in Teaspoons:** Instant visual conversion of total/added sugars into physical teaspoons/cubes (~4g each, rounded to nearest 0.5) to highlight hidden sugars.
- 📦 **"Eat the Whole Packet" Calculator:** One-click multiplier comparing single-serve claims against true whole-packet contents.
- 🎯 **Transparent Scoring (v1.0):** 0–100 category-aware score with exact itemized reasons based on WHO & Nutri-Score standards.
- 🛡️ **Grounded AI Explainer:** Language model explains validated data only, reinforced by a strict numeric verification post-check.
- 🏆 **FoodLens Quest:** Gamified learning layer rewarding literacy, data corrections, and comparisons (XP, levels, streaks, badges, and mini-games like *"Guess Before You Scan"* and *"The Serving Trap"*).

---

## 🏗️ Architecture

```
Client (Streamlit MVP / Web / Mobile)
       │ HTTP / JSON
       ▼
 FastAPI Backend (`api/`)
  ├── /api/scan/barcode       ──> Decode & EAN-13 Checksum ──> Local DB / Open Food Facts
  ├── /api/scan/label         ──> Image Preprocessing ──> OCR ──> Parser ──> Confidence
  ├── /api/scan/confirm       ──> Validation Rules ──> Persistent DB ──> XP Award
  ├── /api/nutrition/calculate──> Portion Calculator (100g / Serving / Packet / Custom)
  ├── /api/compare            ──> Per-100g Side-by-Side Comparison Matrix
  ├── /api/advice             ──> Grounded AI Advisor (Strict Number Post-Check)
  ├── /api/profile/*          ──> DPDP Act Profile, Minor Consent, Export, Erasure
  ├── /api/household/*        ──> Family Profiles CRUD, Export, Erasure
  ├── /api/family/check       ──> Multi-Member Family Food Fit & Allergen Matrix
  ├── /api/reports/*          ──> Wrong Data Submissions, Consensus & Status Checks
  ├── /api/admin/*            ──> Protected Review Queue, Revisions & Metrics
  ├── /api/personal-fit       ──> Demographic-Aware RDA Fit & Deterministic Allergen Alerts
  ├── /api/sugar/analyze      ──> Hidden Sugar Detector, Sugar Splitting & Conflict Cross-Check
  └── /api/quest/*            ──> XP, Leveling, Streak Freezes, Badges, Mini-Games
       │
       ▼
 Pure Python Core Domain (`foodlens/`)
  ├── units.py            (Deterministic conversions: kJ↔kcal, mg↔g, salt↔sodium, teaspoons)
  ├── nutrition.py        (Nutrient dataclass, linear scaling, None preservation)
  ├── validation.py       (Ranges, subset relationships, Atwater energy cross-check)
  ├── barcode.py          (EAN-13 check digit, India 890 detection, OpenCV decoding)
  ├── parser.py           (Regex + nutrient dictionary, basis detection, comma decimals)
  ├── scoring.py          (Category thresholds, WHO/Nutri-score informed, versioned)
  ├── ingredients.py      (Ordered parsing, INS/E-number lookup, allergen detection)
  ├── allergens.py        (100% deterministic allergen cross-check & regional synonyms)
  ├── personal_fit.py     (ICMR-NIN 2020 RDA calculator & under-18 safety rules)
  ├── family_fit.py       (Multi-member household fit engine, allergen matrix, DPDP rules)
  ├── narration.py        (Deterministic Hindi & English spoken audio script builder)
  ├── tts/                (BrowserSpeechProvider Web Speech API & cached ServerTTSProvider)
  ├── report_checks.py    (Plausibility, duplicate detection, consensus & priority scoring)
  ├── image_security.py   (8MB limit, EXIF/GPS stripping, re-encoding)
  ├── sugar_detector.py   (Sugar aliases, rapidfuzz OCR typo tolerance, sugar splitting)
  ├── advisor.py          (Grounded explanations, strict hallucination guardrail)
  └── gamification/       (XP engine, streak freezes, badge unlock rules, mini-games)
       │
       ▼
 SQLite Database (`db/`) with Alembic Migrations
```

---

## 🚀 Quick Start

### 1. Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/foodlens-ai/foodlens-ai.git
cd foodlens-ai

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Streamlit Application
Launch the interactive web UI:
```bash
streamlit run app/Home.py
```
Open your browser at `http://localhost:8501`.

### 3. Run the FastAPI REST Server
Start the backend API server:
```bash
uvicorn api.main:app --reload --port 8000
```
Explore interactive Swagger documentation at `http://localhost:8000/docs`.

---

## 🧪 Running Tests & Evaluation Benchmarks

Run the complete 40-test suite:
```bash
pytest
```

Run property-based and benchmark evaluations:
```bash
pytest tests/unit/test_nutrition.py      # Property scaling tests
pytest tests/eval/test_evaluation_benchmark.py # Accuracy & Groundedness benchmarks
```

---

## 📁 Project Structure

```
foodlens-ai/
├── AGENTS.md                  # Project rules & architecture guidelines
├── README.md                  # Project overview & documentation
├── requirements.txt           # Python dependencies
├── pyproject.toml             # Packaging & pytest configuration
├── .env.example               # Environment variables template
├── docs/                      # Technical specifications & reports
│   ├── blueprint.md           # The complete project blueprint
│   ├── architecture.md        # Architectural diagrams & decisions
│   ├── scoring_method.md      # Category-aware nutritional scoring specification
│   ├── prompts.md             # Grounded LLM prompts & guardrails
│   ├── eval_report.md         # OCR & Parser evaluation benchmarks
│   └── limitations.md         # Known edge cases and future roadmap
├── foodlens/                  # Pure Python core domain logic (NO UI imports)
│   ├── units.py               # Unit normalization
│   ├── nutrition.py           # Nutrient dataclass & scaling calculator
│   ├── validation.py          # Plausibility, subset, and energy balance rules
│   ├── barcode.py             # Barcode decoding & EAN-13 checksum validation
│   ├── off_client.py          # Open Food Facts API client with caching
│   ├── ocr.py                 # Image preprocessing & OCR pipeline
│   ├── parser.py              # Nutrient dictionary & regex parser
│   ├── scoring.py             # Category-aware transparent scoring engine
│   ├── ingredients.py         # Ingredient categorization & allergen detection
│   ├── advisor.py             # Grounded AI explanation & strict number-verification guardrail
│   ├── gamification/          # FoodLens Quest gamification layer
│   │   ├── xp.py              # XP awarding rules & anti-spam caps
│   │   ├── streaks.py         # Daily streaks & streak freeze logic
│   │   ├── badges.py          # Milestone badges
│   │   └── challenges.py      # Daily challenges & mini-games
│   └── config/
│       ├── nutrient_dictionary.json
│       ├── category_thresholds.yaml
│       └── ingredient_table.csv
├── db/                        # Database layer (SQLite via SQLAlchemy)
│   ├── models.py
│   └── session.py
├── api/                       # FastAPI REST API
│   ├── main.py
│   ├── deps.py
│   ├── schemas.py
│   └── routes/
├── app/                       # Streamlit UI
│   ├── Home.py
│   ├── pages/
│   │   ├── 1_Scan.py
│   │   ├── 2_Result.py
│   │   ├── 3_Compare.py
│   │   ├── 4_Quest.py
│   │   ├── 5_History.py
│   │   └── 6_Settings.py
│   ├── components/
│   └── assets/
├── data/                      # Evaluation data & gold labels
│   └── sample_products.csv
└── tests/                     # Test suite (40 automated tests)
    ├── unit/
    ├── integration/
    └── eval/
```

---

## 💼 Portfolio & Resume Summary
> **FoodLens AI:** Built a packaged-food analyzer using Python, FastAPI, OCR, and Gemini that extracts nutrition labels, validates them with rule-based checks, calculates portion-level nutrition deterministically, and explains results with grounded AI; added a gamified learning layer to boost label literacy.

