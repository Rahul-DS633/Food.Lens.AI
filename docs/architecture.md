# FoodLens AI — Architecture & System Design

## 1. Overview
FoodLens AI is a packaged-food intelligence system that combines deterministic nutrition calculation, OCR label extraction, transparent category-aware scoring, grounded LLM explanations, and an educational gamification layer ("FoodLens Quest").

```
Client (Streamlit MVP / React / Mobile)
       │ HTTP / JSON
       ▼
 FastAPI Backend (`api/`)
  ├── /api/scan/barcode       ──> Decode & EAN-13 Checksum ──> DB Cache / OFF Client
  ├── /api/scan/label         ──> Image Preprocessing ──> OCR ──> Parser ──> Confidence
  ├── /api/scan/confirm       ──> Validation Rules ──> Persistent DB ──> XP Award
  ├── /api/nutrition/calculate──> Deterministic Portion Calculator (100g/serving/packet/custom)
  ├── /api/compare            ──> Per-100g Side-by-Side Comparison Matrix
  ├── /api/advice             ──> Grounded AI Advisor (Strict Number Post-Check)
  └── /api/quest/*            ──> XP, Leveling, Streak Freezes, Badges, Mini-Games
       │
       ▼
 Pure Python Core Domain (`foodlens/`)
  ├── units.py            (Deterministic unit conversion: kJ↔kcal, mg↔g, salt↔sodium)
  ├── nutrition.py        (Nutrient dataclass, linear scaling, None preservation)
  ├── validation.py       (Ranges, subset relationships, Atwater energy cross-check)
  ├── barcode.py          (EAN-13 check digit, India 890 detection, OpenCV decoding)
  ├── parser.py           (Regex + nutrient dictionary, basis detection, comma decimals)
  ├── scoring.py          (Category thresholds, WHO/Nutri-score informed, versioned)
  ├── ingredients.py      (Ordered parsing, INS/E-number lookup, allergen detection)
  ├── advisor.py          (Grounded explanations, strict hallucination guardrail)
  └── gamification/       (XP engine, streak freezes, badge unlock rules, mini-games)
       │
       ▼
 Database Layer (`db/`)
  ├── SQLite (via SQLAlchemy 2.0 ORM)
  └── Models: products, nutrition, ingredients, extractions, scans, users, progress, achievements
```

## 2. Core Architectural Principles
1. **Deterministic Code Calculates; LLM Only Explains**: All math (scaling, unit conversion, energy cross-checks, scores) is implemented in pure Python. The language model never performs calculations.
2. **Never Zero-Fill Missing Values**: If a nutrient is absent from a label, it remains `None`. Scaling preserves `None`.
3. **Provenance & Confidence**: Every value tracks its origin (`api`, `ocr`, `user`, `manual`) and confidence score ($0.0$ to $1.0$).
4. **Neutral Language**: Objective factual reporting without moralizing food ("good" vs "bad") or making medical claims.
5. **User Agency**: The user is always presented with extracted values and can edit or override any field.

## 3. Data Reconciliation Rule
When OCR extraction and the product database (Open Food Facts / Local Cache) disagree on a value:
- The UI displays both values alongside their respective sources (`OCR` vs `OFF/API`).
- The user is invited to select the verified ground truth.
- The confirmed choice is stored with `verification_status="user_confirmed"` and awards the user $+15\text{ XP}$ for verified data contribution.
