# FoodLens AI — Claim Checker & Front-of-Pack Verification Specification

## 1. Overview & Objective
Packaged food products frequently carry prominent front-of-pack marketing claims such as *"No Added Sugar"*, *"High Protein"*, *"100% Whole Wheat"*, *"Zero Trans Fat"*, and *"100% Natural"*.

The **Claim Checker** module provides a deterministic, transparent, and legally neutral verification engine that:
1. Compares declared front-of-pack claims with laboratory nutrition facts, ordered ingredient lists, and hidden sugar detector reports.
2. Evaluates claims according to statutory benchmarks from the **Food Safety and Standards (Advertising and Claims) Regulations, 2018** (amended 2021) and **Codex Alimentarius (CAC/GL 23-1997)**.
3. Categorizes each claim into one of five unambiguous statuses with supporting evidence:
   - `SUPPORTED`: Label numbers meet or exceed statutory benchmark thresholds.
   - `PARTLY_SUPPORTED`: Ingredients qualify partially (e.g., whole grain present but secondary to refined flour).
   - `NOT_SUPPORTED`: The label values do not appear to support this claim based on declared nutrients.
   - `CANNOT_VERIFY`: Crucial label data (e.g. nutrient omitted from panel, serving size unknown) is missing.
   - `NOT_CHECKABLE`: Vague marketing terms (*"natural"*, *"healthy"*, *"wholesome"*) lacking statutory nutrient definitions.

---

## 2. Strict Legal Neutrality & Safe Wording

1. **Approved Phrasing**:
   - Approved: *"The label values do not appear to support this claim based on declared nutrients."*
   - Strictly Banned: `false`, `misleading`, `fraud`, `cheat`, `lie`, `deceptive`, `fake`.
   - Never accuse or attack brands.
2. **Category Nuance Disclaimers**:
   - Every verification output carries the mandatory footnote:
     > *"Based on the label data we have; claim rules can differ by product category."*
3. **Automated Safety Scanner**:
   - Continuous CI verification via `tests/unit/test_claims_safety.py` scanning code, configs, and output strings.

---

## 3. Statutory Regulatory Benchmarks (`foodlens/config/claims.yaml`)

Thresholds are established according to FSSAI (2018) Schedule-I and Codex standards:

| Rule ID | Category | Statutory Benchmark | Regulatory Source |
| :--- | :--- | :--- | :--- |
| `sugar_free` | Sugar | $\le 0.5\text{ g} / 100\text{ g}$ (or $100\text{ ml}$) | FSSAI 2018 Schedule-I, Codex CAC/GL 23-1997 |
| `low_sugar` | Sugar | $\le 5.0\text{ g} / 100\text{ g}$ (solid), $\le 2.5\text{ g} / 100\text{ ml}$ (liquid) | FSSAI 2018 Schedule-I, Codex CAC/GL 23-1997 |
| `no_added_sugar` | Sugar | $0\text{ g}$ added sugar + 0 added sugars/syrups/concentrates detected | FSSAI 2018 Schedule-I |
| `source_of_protein` | Protein | $\ge 6.0\text{ g} / 100\text{ g}$ (solid), $\ge 3.0\text{ g} / 100\text{ ml}$ (liquid) | FSSAI 2018 Schedule-I (10% RDA) |
| `high_protein` | Protein | $\ge 12.0\text{ g} / 100\text{ g}$ (solid), $\ge 6.0\text{ g} / 100\text{ ml}$ (liquid) | FSSAI 2018 Schedule-I (20% RDA) |
| `source_of_fibre` | Fibre | $\ge 3.0\text{ g} / 100\text{ g}$ (solid), $\ge 1.5\text{ g} / 100\text{ ml}$ (liquid) | FSSAI 2018 Schedule-I, Codex CAC/GL 23-1997 |
| `high_fibre` | Fibre | $\ge 6.0\text{ g} / 100\text{ g}$ (solid), $\ge 3.0\text{ g} / 100\text{ ml}$ (liquid) | FSSAI 2018 Schedule-I, Codex CAC/GL 23-1997 |
| `fat_free` | Fat | $\le 0.5\text{ g} / 100\text{ g}$ | FSSAI 2018 Schedule-I, Codex CAC/GL 23-1997 |
| `low_fat` | Fat | $\le 3.0\text{ g} / 100\text{ g}$ (solid), $\le 1.5\text{ g} / 100\text{ ml}$ (liquid) | FSSAI 2018 Schedule-I, Codex CAC/GL 23-1997 |
| `low_saturated_fat`| Fat | $\le 1.5\text{ g} / 100\text{ g}$ (solid), $\le 0.75\text{ g} / 100\text{ ml}$ (liquid) | FSSAI 2018 Schedule-I |
| `no_trans_fat` | Fat | $\le 0.2\text{ g} / 100\text{ g}$ | FSSAI 2018 Schedule-I |
| `low_sodium` | Sodium | $\le 120.0\text{ mg} / 100\text{ g}$ ($\approx 0.3\text{ g}$ salt) | FSSAI 2018 Schedule-I, Codex CAC/GL 23-1997 |
| `whole_grain` | Grain | Position #1 in ingredient list; maida absent or subordinate | FSSAI Advertising Regulations 2018 |
| `multigrain` | Grain | $\ge 2$ distinct edible grains declared | FSSAI Advertising Regulations 2018 |
| `no_maida` | Grain | Refined wheat flour absent from ingredient list | FSSAI Labelling Standards |
| `vague_terms` | Buzzwords | *"Natural"*, *"Healthy"*, *"Wholesome"* have no statutory numerical thresholds | Regulatory standard note |

---

## 4. Architecture & Data Flow

```
Front Panel Text / User Input Chips
                │
                ▼
     ┌──────────────────────┐
     │     ClaimChecker     │ ◄── foodlens/config/claims.yaml
     └──────────┬───────────┘
                │
       Deterministic Check
       ├── Scale per-serving linearly to 100g (or CANNOT_VERIFY)
       ├── Cross-reference SugarDetector report
       ├── Evaluate ingredient order & flour ranking
       └── Compare numeric bounds with operator (<=, >=)
                │
                ▼
     ┌──────────────────────┐
     │  ClaimCheckSummary   │ ──► AIAdvisor.explain_claim_check()
     └──────────┬───────────┘
                │
                ▼
     FastAPI (/api/claims/check)
                │
                ▼
     Streamlit (app/components/claim_chips.py)
```

---

## 5. API Reference

### `POST /api/claims/check`

#### Request Body
```json
{
  "product_id": 1,
  "claims": ["High Protein", "No Added Sugar", "100% Natural"]
}
```

#### Response
```json
{
  "total_claims": 3,
  "supported_count": 2,
  "partly_supported_count": 0,
  "not_supported_count": 0,
  "cannot_verify_count": 0,
  "not_checkable_count": 1,
  "summary_sentence": "2 of 3 claims supported by label data.",
  "results": [
    {
      "claim_text": "High Protein",
      "rule_id": "high_protein",
      "status": "SUPPORTED",
      "evidence": [{"field": "protein_g", "value": 14.0, "basis": "per_100g"}],
      "threshold_value": 12.0,
      "threshold_operator": ">=",
      "threshold_source": "FSSAI Claims Reg 2018 Schedule-I",
      "confidence": 1.0,
      "missing_fields": [],
      "neutral_explanation": "Declared protein (14.0 g / 100 g) meets the statutory threshold (>= 12.0 g / 100 g).",
      "disclaimer": "Based on the label data we have; claim rules can differ by product category."
    }
  ],
  "ai_summary": {
    "summary": "Evaluated 3 front-of-pack claims for Apex Protein Bar: 2 of 3 claims supported by label data. Claim 'High Protein' is supported by label data.",
    "is_grounded": true,
    "disclaimer": "Based on the label data we have; claim rules can differ by product category."
  }
}
```
