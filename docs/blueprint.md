# FoodLens AI — Complete Project Blueprint
Version 2.0 · 5 November 2026 · Improved and expanded from the original FoodLens AI Project Guide

## 1. Decision Summary
**Should FoodLens be a game?** Recommendation: build a serious food-intelligence tool with a game layer on top. Do not build a full game.

| Question | Answer |
| :--- | :--- |
| **Core product** | Label scanner + nutrition calculator + explainer (trustworthy, deterministic) |
| **Game element** | "FoodLens Quest": XP, levels, streaks, badges, daily challenges, mini-games |
| **What gets rewarded** | Learning, scanning, verifying data, comparing products. Never eating less or choosing "low-calorie" foods |
| **When to build it** | After the core scan → extract → calculate → explain path works (Phase 2, about Days 20–26) |
| **Tech impact** | Game layer is only extra tables + a small XP service. Core engines stay unchanged |

**Why not a full game:**
1. Users must trust health-adjacent numbers, and game mechanics can make results feel arbitrary.
2. A 30-day solo build cannot support both a reliable OCR pipeline and game design.
3. Rewarding restriction or "perfect scores" can encourage unhealthy eating behaviour.
4. Recruiters and judges value accuracy, evaluation and engineering rigour more than game polish.

**Why gamify at all:** label reading is boring and people abandon food apps quickly. Streaks, quests and "guess before you scan" challenges turn label literacy into a habit and make the demo memorable.

---

## 2. Vision and Positioning
**One-line pitch:** Point your camera at any packaged food and learn what is really inside, how much you are actually eating, and how it compares, with every number traceable to its source.

### Problem
Nutrition labels are confusing: per-100g vs per-serving, hidden sugars, unfamiliar additives, packets that contain 2–3 servings.

### Principles
1. Deterministic code calculates; the language model only explains validated data.
2. Never invent or zero-fill missing values.
3. Every value carries provenance (API, OCR, manual) and confidence.
4. Neutral language: no "good/bad food", no medical diagnosis, no disease claims.
5. The user can always correct the extraction.

### Differentiators
Indian packaged-food focus, OCR fallback when the barcode is unknown, "eat the whole packet" calculator, sugar-in-teaspoons visualisation, transparent score, Hindi + English, and a game layer that rewards label literacy.

---

## 3. Scope: MVP, Version 2, Version 3
*Rule: do not start a lower-priority item until the one above it is tested.*

| Priority | Feature | Phase |
| :--- | :--- | :--- |
| **Must** | Image upload, barcode lookup (Open Food Facts), OCR extraction, correction screen | MVP |
| **Must** | Unit normalisation, per-100g / per-serving / consumed / whole-packet calculator | MVP |
| **Must** | Validation rules, missing-data handling, provenance | MVP |
| **Must** | Ingredient and allergen explanations, transparent score, grounded AI explanation | MVP |
| **Should** | Product comparison, scan history, SQLite persistence | MVP / v2 |
| **Should** | FoodLens Quest (XP, streaks, badges, daily challenge) | v2 |
| **Could** | Hindi/English toggle, accounts (Firebase), weekly summary | v2 |
| **Later** | Flutter/PWA mobile app, offline mode, custom label classifier, recommendations | v3 |

---

## 4. Gamification Design: FoodLens Quest
### 4.1 Design rules (safety first)
- Reward actions and knowledge: scanning, correcting a label, finishing a lesson, comparing products.
- Never reward low calories, low sugar or a high health score. Never show "you failed" because of what someone ate.
- No streak-loss shaming; use "streak freeze" days and gentle wording.
- No weight, body-image or calorie-restriction goals anywhere in the game layer.
- Cap XP per day and per product to prevent spam scanning.

### 4.2 Mechanics
- **XP**: Scan product +10, confirm/correct extracted fields +15, first scan of a new product +20, compare two products +15, finish a mini-game +10 to +25.
- **Levels**: Label Rookie → Label Reader → Label Detective → Nutrition Navigator → Food Intelligence Pro.
- **Streaks**: Days with at least one scan or lesson; weekly streak freeze.
- **Badges**: First Scan, Barcode Hunter (10 scans), Sharp Eyes (10 corrections accepted), Sugar Spotter, Serving Size Sleuth, Comparison Champion, Hindi Explorer.
- **Daily challenge**: "Find a packaged food with a per-serve size smaller than the packet", "Compare two biscuits".
- **Collections**: Category stamps (biscuits, chips, namkeen, drinks, cereals) filled as the user scans.

### 4.3 Mini-games (pick two for v2)
1. **Guess Before You Scan**: user guesses sugar per serving (slider), the scan reveals the truth, closeness earns XP. Teaches real label values.
2. **Label Detective**: a real label image with one hidden clue (serving size, added sugar, allergen); user finds it.
3. **Sugar Cubes**: converts grams of sugar to teaspoons (about 4 g each) with stacked cube animation for the chosen portion.
4. **Serving Trap**: "How many servings are in this packet?" quiz generated from scanned products.

### 4.4 Data contribution loop
When a user corrects an OCR field and the correction is validated, award XP and store it as a verified record. This improves your dataset and gives you real evaluation data.

---

## 5. Users and Core Journeys
**Personas:** a student comparing snacks; a parent checking allergens and sugar; a gym-goer checking protein bars; a curious user playing quests.

### Primary journey (scan path)
1. Open app, tap Scan.
2. Barcode detected, then lookup in cache, then Open Food Facts.
3. If the record is missing or incomplete, prompt for nutrition-panel and ingredients photos.
4. OCR extracts fields; low-confidence fields are highlighted.
5. User confirms or edits fields (XP awarded).
6. Validation runs; conflicts are shown, not hidden.
7. User picks portion (1 serving, grams, whole packet).
8. Result screen: nutrition for portion, flags, score with reasons, ingredient notes, AI explanation.
9. Save to history, compare, and receive quest progress.

---

## 6. System Architecture
```
Client (Streamlit MVP → React/Flutter later)
│ REST (JSON)
▼
FastAPI backend
├─ barcode_service     → decode + EAN checksum
├─ product_service     → cache → Open Food Facts → manual
├─ ocr_service         → preprocess → OCR → parser → confidence
├─ validation          → unit + plausibility + consistency rules
├─ nutrition_engine    → deterministic calculations
├─ scoring_engine      → versioned, category-aware score
├─ ingredient_engine   → allergens + explanations
├─ ai_service          → Gemini, grounded on validated JSON
└─ gamification        → XP, streaks, badges, challenges
▼
SQLite (MVP) → PostgreSQL (later) · Object storage for images
```

**Design decision:** put all logic in a plain Python package (`foodlens/`). FastAPI and Streamlit both import it. This keeps the UI swappable and makes unit testing easy.

**Reconciliation rule:** when OCR and the product database disagree for a field, show both with their sources and ask the user to choose. Store original and normalised values separately.

---

## 7. Technology Stack
- **UI (MVP):** Streamlit (session state, `st.camera_input`, Plotly, custom CSS for game look)
- **Backend:** FastAPI + Pydantic
- **Barcode:** OpenCV / pyzbar / zxing-cpp (EAN-13/UPC checksum validation)
- **Image:** OpenCV, Pillow (Resize, deskew, CLAHE contrast, perspective correction)
- **OCR:** EasyOCR / Tesseract / PaddleOCR / Gemini vision fallback
- **Data:** Pandas, NumPy
- **AI:** Gemini API (Explanations only, JSON in, text out)
- **Database:** SQLite via SQLAlchemy
- **Charts:** Plotly (Macro bars, comparison radar, sugar cubes)
- **Testing:** pytest, Hypothesis

---

## 8. Data Sources and Data Quality
- **Open Food Facts:** barcodes, names, ingredients, nutrition, images. Coverage for Indian products is uneven.
- **USDA FoodData Central:** generic composition only; never a substitute for a specific packet's label.
- **FSSAI:** authority for Indian labelling rules; check current amendments before finalising display rules.
- **Verified Dataset:** Gold standard for evaluation.
- **Metadata stored per product:** source, retrieval date, verification status (`api`, `ocr`, `user_confirmed`, `manual`), original label text, data-quality grade (A complete, B partial, C minimal).

---

## 9. Core Engines Specification

### 9.1 Barcode
Decode, strip whitespace, validate length and checksum (EAN-13 for Indian products starting 890), then query cache before API. Handle: not found, duplicate records, malformed codes, timeouts (fall back to OCR flow).

### 9.2 OCR and Extraction Pipeline
1. Capture or upload up to three images: front, nutrition panel, ingredients.
2. Detect orientation and crop panel.
3. Enhance: grayscale, denoise, CLAHE, deskew, upscale small text.
4. Run OCR; keep raw text, bounding boxes and confidence.
5. Parse with nutrient dictionary and regex for `value + unit`.
6. Detect basis: per 100 g, per 100 ml, per serving (with serving size).
7. Normalise units (kJ→kcal, mg↔g) while keeping original.
8. Validate, flag low confidence, and send to correction screen.

### 9.3 Validation Rules
- **Range:** Each nutrient is within plausible per-100g limits (e.g. sugar ≤ 100 g).
- **Subset:** Sugars ≤ carbohydrates; saturated fat ≤ total fat; added sugar ≤ total sugar.
- **Energy cross-check:** kcal ≈ 4×protein + 4×carbs + 9×fat (+2×fibre); flag if gap exceeds ~15–20%.
- **Unit confusion:** Sodium of 400 g is impossible; probable mg/g mix-up.
- **Basis:** Per-serve values must have a serving size to convert.
- **Salt vs sodium:** Salt ≈ sodium × 2.5; detect which is printed.
- **Missing:** Keep `None`; never convert to 0.

### 9.4 Nutrition Engine
A nutrient is an object, not a bare number:
```python
@dataclass(frozen=True)
class Nutrient:
    value: float | None
    unit: str            # g, mg, kcal
    basis: str           # per_100g | per_100ml | per_serving
    source: str          # api | ocr | user | manual
    confidence: float    # 0..1

def scale(n: Nutrient, grams: float) -> Nutrient | None:
    if n.value is None:
        return None      # never zero-fill
    return replace(n, value=round(n.value * grams / 100, 2))
```
Supports: 100 g, serving, custom grams, number of servings, whole packet (net weight), and per-100 ml for beverages. Property tests: scaling by 100 g returns original; scaling is linear; None stays None.

### 9.5 Scoring Engine (v1)
Six-component category-aware formula:
- Negative components: sugar, saturated fat, sodium, energy density.
- Positive components: protein, fibre.
- Thresholds per category (drinks, snacks, cereals, spreads, etc.).
- Output: total score, band, per-component points, reason list.
- If > 2 components missing, show "Insufficient data".
- Store `scoring_version`.

### 9.6 Ingredient Intelligence
- Parse list into ordered ingredients.
- Map to curated table: category, plain-language role, allergen flag.
- Detect declared allergens (milk, soy, peanut, gluten/wheat, nuts, egg).
- Allergen wording: "No allergen detected in the text we could read", never "allergen-free".
- Approved additives are explained, not condemned.

### 9.7 AI Advisor
- Input: validated JSON. Output: structured explanation.
- Guardrails: never invent values; cite basis in every sentence about a number; no diagnosis or disease claims; admit insufficient data.
- Strict post-check: verify every number in the response appears in the input JSON.

---

## 10. Database Schema
- `products`: id, barcode UNIQUE, name, brand, category, net_weight_g, serving_size_g, image_url, source, retrieved_at, verification_status, quality_grade
- `nutrition`: id, product_id, basis, energy_kcal, protein_g, carbs_g, sugars_g, added_sugar_g, fat_g, sat_fat_g, trans_fat_g, fibre_g, sodium_mg, raw_label_json, normalised_json, field_sources_json
- `ingredients`: id, product_id, position, name, category, explanation, allergen_flag
- `extractions`: id, scan_id, ocr_engine, raw_text, avg_confidence, field_confidence_json, user_corrections_json
- `scans`: id, user_id, product_id, source_type, consumed_g, score, scoring_version, created_at
- `users`: id, display_name, language, created_at
- `user_progress`: user_id PK, xp, level, current_streak, longest_streak, last_active_date, streak_freezes
- `xp_events`: id, user_id, event_type, xp, ref_id, created_at
- `achievements`: id, code, title, description, rule_json
- `user_achievements`: user_id, achievement_id, earned_at
- `challenges`: id, date, type, config_json
- `challenge_attempts`: id, user_id, challenge_id, result_json, xp
