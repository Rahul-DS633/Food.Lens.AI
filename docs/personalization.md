# Personalized Food Fit — Architectural Documentation

## 1. Overview & Guarantees
The **Personalized Food Fit** feature in FoodLens AI tailors packaged food analysis to an individual user's dietary profile (age, optional weight, declared allergies) while upholding all core project tenets:
1. **Deterministic Calculation**: All unit scaling, reference percentages, and allergen matches are computed exclusively by pure Python deterministic functions (`foodlens/personal_fit.py` and `foodlens/allergens.py`).
2. **Never Invent Missing Values**: If a nutrient is missing from the packaging label, its reference percentage remains `None`. It is never assumed to be zero.
3. **Strict Allergen Invariant**: Allergen statuses are restricted to 4 exact values:
   - `CONTAINS_YOUR_ALLERGEN`
   - `MAY_CONTAIN_TRACES`
   - `NONE_DETECTED_IN_READABLE_TEXT`
   - `UNKNOWN`
   *FoodLens never states a product is "safe" or "allergen-free". Every allergen message ends with: "Verify on the pack."*
4. **No Medical Claims / Neutral Tone**: No diagnosis, no disease claims, no BMI profiling, and no weight-loss/gain goals.

---

## 2. Demographic & Safety Guardrails (India DPDP Act 2023)

### 2.1 Minor Protection (Age < 18)
- Under Section 9 of India's Digital Personal Data Protection Act (DPDP Act) 2023, data processing for individuals under 18 requires verifiable parental / guardian consent.
- **Caloric and Weight Targets Disabled**: For users under 18, all calorie-based guidance and weight-based protein calculations ($g / kg$) are disabled. General label information and allergen detection remain fully active.
- A prominent advisory instructs minors to involve a parent or guardian.

### 2.2 Adult Protein Reference Intakes
- For adults ($\ge 18$), if body weight is optionally provided, the protein reference intake is scaled using the **ICMR-NIN (2020)** recommended dietary allowance ($0.83 \text{ g/kg body weight}$).
- If weight is omitted, a standard adult reference of $54.0 \text{ g}$ is used.

---

## 3. Reference Intakes Sourcing (`foodlens/config/reference_intakes.yaml`)
Nutrient reference values are drawn from official regulatory standards:
- **ICMR-NIN 2020**: Recommended Dietary Allowances and Estimated Average Requirements for Indians.
- **FSSAI 2020**: Food Safety and Standards (Labelling and Display) Regulations, Schedule II.
- **WHO 2015**: Guideline: Sugars and Sodium Intake for Adults and Children.

---

## 4. Privacy & Anonymization
- **Name Exclusion**: The user's name is strictly for device display and is **never** transmitted to Gemini or external LLMs.
- **Untrusted Input Protection**: All OCR and label text is treated as untrusted data to defend against prompt injection.
- **Grounding Post-Check**: Every number in the AI advisor's explanation must match an exact number present in the deterministic input payload. Hallucinated numbers are flagged and rejected, falling back to a deterministic template.

---

## 5. User Rights (DPDP Act)
Users can exercise statutory rights directly from the Profile page:
- **Right to Data Portability**: Export all profile and scan history as structured JSON (`/api/profile/{user_id}/export`).
- **Right to Erasure**: Permanently erase all personal profile data and scan history with one click (`DELETE /api/profile/{user_id}`).

---

## 6. Mandatory Disclaimer
> **Disclaimer**: General information, not medical advice. Verify on the pack.
