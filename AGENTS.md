# FoodLens AI — Agent Guidelines & Project Rules

## Core Principles (Absolute Rules — Never Break)
1. **Deterministic Code Calculates; LLM Only Explains Validated Data**:
   All unit conversions, scaling (per 100g, per serving, whole packet, custom grams), energy cross-checks, and scoring arithmetic MUST be performed by pure Python deterministic functions. Never ask or allow an LLM to calculate numbers.
2. **Never Invent or Zero-Fill Missing Values**:
   If a nutrient (e.g. fibre, trans fat, added sugar) is not present on the label or API, its value is `None`. It is NEVER 0.0 unless the label explicitly states 0. `None` remains `None` when scaled.
3. **Every Value Carries Provenance & Confidence**:
   Nutrients are modeled as objects (`Nutrient(value, unit, basis, source, confidence)`), tracking source (`api`, `ocr`, `user`, `manual`) and confidence (0.0 to 1.0).
4. **Neutral Language**:
   No "good food / bad food", no moralizing, no medical diagnosis, no disease-causation claims ("cures cancer", "causes diabetes"). Present verified facts with reference thresholds.
5. **User Agency / Always Correctable**:
   The user can always review, correct, or override any extracted field. When OCR and the product database disagree, present both options to the user.
6. **Write Tests With Every Module**:
   Every core engine module must have accompanying unit and property tests. Gold-label tests act as the referee. Never relax validation or tests to make faulty code pass.

## Architecture & Project Structure
Put all domain and business logic in `foodlens/` (pure Python, zero UI dependencies).
FastAPI (`api/`) and Streamlit (`app/`) import `foodlens/`.

```
foodlens-ai/
├── AGENTS.md                  # This file (project rules)
├── README.md                  # Project overview & setup instructions
├── requirements.txt           # Dependencies
├── pyproject.toml             # Project config & packaging
├── .env.example               # Environment variables template
├── docs/
│   ├── blueprint.md           # The complete project blueprint
│   ├── architecture.md        # Architectural diagrams & decisions
│   ├── scoring_method.md      # Category-aware nutritional scoring specification
│   ├── prompts.md             # Grounded LLM prompts & guardrails
│   └── eval_report.md         # OCR & Parser evaluation benchmarks
├── foodlens/                  # Pure Python core domain logic (NO UI imports)
│   ├── __init__.py
│   ├── units.py               # Unit normalization (kJ->kcal, mg<->g, ml<->g)
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
│   │   ├── __init__.py
│   │   ├── xp.py              # XP awarding rules & anti-spam caps
│   │   ├── streaks.py         # Daily streaks & streak freeze logic
│   │   ├── badges.py          # Milestone badges
│   │   └── challenges.py      # Daily challenges & mini-games
│   └── config/
│       ├── nutrient_dictionary.json
│       ├── category_thresholds.yaml
│       └── ingredient_table.csv
├── db/                        # Database layer (SQLite via SQLAlchemy)
│   ├── __init__.py
│   ├── models.py
│   └── session.py
├── api/                       # FastAPI REST API
│   ├── main.py
│   ├── deps.py
│   ├── schemas.py
│   └── routes/
│       ├── scan.py
│       ├── nutrition.py
│       ├── products.py
│       ├── compare.py
│       ├── advice.py
│       ├── quest.py
│       └── history.py
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
│   │   ├── nutrient_card.py
│   │   ├── score_ring.py
│   │   ├── sugar_cubes.py
│   │   ├── xp_bar.py
│   │   └── badge.py
│   └── assets/
│       └── theme.css
├── data/                      # Evaluation data & gold labels
│   ├── gold_labels/
│   └── sample_products.csv
└── tests/                     # Test suite
    ├── unit/
    ├── integration/
    └── eval/
```

## Coding & Style Guidelines
- Pure Python for `foodlens/`: Use type hints everywhere, dataclasses / Pydantic models where appropriate.
- Keep functions small and modular.
- Error codes must be descriptive and structured (`LOW_CONFIDENCE`, `PRODUCT_NOT_FOUND`, `VALIDATION_FAILED`).
- Guardrails for AI: Every numeric claim made by Gemini must be verified against the input JSON. If a hallucinated number is detected, reject or regenerate the explanation.
