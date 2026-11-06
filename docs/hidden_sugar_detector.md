# Hidden Sugar Detector — Technical Documentation

## 1. Overview & Objectives
Manufacturers often divide sugar into multiple distinct ingredients (such as *sugar, invert syrup, glucose syrup, date paste*) to push individual sugar items down the descending weight-ordered ingredient statement. This practice is known as **sugar splitting**.

The **Hidden Sugar Detector** identifies, categorizes, and explains every sugar, syrup, fruit concentrate, carbohydrate bulking agent, and non-sugar sweetener present in an ingredient statement. It translates grams of sugar into intuitive teaspoon metrics ($4\text{g} = 1\text{ tsp}$, rounded to nearest $0.5$) and cross-checks the declared nutrition label for discrepancies.

---

## 2. Core Architectural Guarantees

1. **Deterministic Calculation**: All alias parsing, tokenization, fuzzy matching, and teaspoon calculations are pure Python deterministic functions (`foodlens/sugar_detector.py`).
2. **Descending Weight Order Invariant**: Ingredient positions indicate descending weight order by statutory labelling law. Position is **never** used to estimate exact gram quantities.
3. **Never Invent Missing Values**: If a label omits added sugar or total sugars, the value remains `None`. Teaspoon metrics explicitly state whether they derive from *added sugar* or *total sugars*.
4. **Classification Transparency**:
   - `SUGARS`, `SYRUPS`, `CONCENTRATES`: Identified as caloric added sugars (`is_added = "yes"`).
   - `AMBIGUOUS` (lactose, milk solids): May be naturally occurring milk components; **never** categorized as added sugars.
   - `CARB_FILLERS` (maltodextrin, dextrin): Flagged separately with neutral digestive explanations; **never** counted in sugar totals.
   - `NON_SUGAR_SWEETENERS` (stevia, sucralose, aspartame, polyols): Non-caloric or intense sweeteners; tracked separately and **never** counted as sugars.
5. **Neutral Tone**: Zero disease claims ("causes diabetes"), zero "good/bad food" labeling, zero moralizing language.

---

## 3. Sugar Splitting & Label Conflict Heuristics

### 3.1 Sugar Splitting
- **Definition**: When 3 or more distinct added sugar aliases are detected in a single ingredient list:
  $$\text{distinct\_sugar\_names} \ge 3 \implies \text{sugar\_splitting} = \text{True}$$
- Highlights the collective predominance of added sugars across the product recipe.

### 3.2 Label Conflict Cross-Check
- If the nutrition facts table reports $0\text{g}$ added sugar, but one or more ingredients in the ingredient statement are classified under `is_added == "yes"` (e.g. *Invert Sugar, Liquid Glucose*):
  - $\rightarrow \text{label\_conflict} = \text{True}$
  - Both facts are presented side-by-side for consumer literacy and transparency.

---

## 4. Teaspoon Calculation Formula
$$\text{Teaspoons} = \frac{\text{Grams}}{4.0}, \quad \text{rounded to nearest } 0.5$$

- Uses `added_sugar_g` when declared on the packaging.
- Falls back to `total_sugars_g` if added sugar is not reported, with an explicit advisory label: *"based on total sugars"*.

---

## 5. RapidFuzz Typographical Matcher
To accommodate real-world mobile OCR typos (e.g. `dextroze`, `invertt syrup`, `glukose`), the detector employs `rapidfuzz.fuzz.token_sort_ratio` with an acceptance threshold of $\ge 85$:
- Exact matches: `confidence = 1.0`, `match_type = "exact"`.
- Fuzzy matches: `confidence < 1.0`, `match_type = "fuzzy"` (flagged as possible OCR typo).
- Negative filters prevent false matches on non-sugar terms such as *sugarcane vinegar* (acetic acid), *cane vinegar*, and *sugar beet fiber*.

---

## 6. Regulatory References
- **FSSAI (2020)**: Food Safety and Standards (Labelling and Display) Regulations.
- **US FDA 21 CFR 101.4**: Designation of ingredients in order of predominance.
- **WHO (2015)**: Guideline on Sugars Intake for Adults and Children.
