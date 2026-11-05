# FoodLens Transparent Scoring Methodology

**Version:** 1.0.0  
**References:** WHO Regional Nutrient Profile Models, Nutri-Score Technical Specifications, FSSAI Labelling Regulations.

---

## 1. Objective
To provide a transparent, 0–100 category-aware nutritional quality score that rewards balanced macronutrient composition and penalizes excessive sugar, saturated fat, sodium, and caloric density, without moralizing food choices.

---

## 2. Six-Component Formula
Scores are evaluated on standardized **per-100g** (or per-100ml for beverages) values.

### A. Negative Components (Penalties)
1. **Total Sugars ($g/100g$)**: Up to $-25$ points for high sugar exceeding category limits.
2. **Saturated Fatty Acids ($g/100g$)**: Up to $-20$ points for high saturated fat.
3. **Sodium ($mg/100g$)**: Up to $-20$ points for excessive sodium levels ($>600\text{ mg}$ for solid foods, $>50\text{ mg}$ for drinks).
4. **Energy Density ($kcal/100g$)**: Up to $-10$ points for high caloric density.

### B. Positive Components (Bonuses)
5. **Protein ($g/100g$)**: Up to $+12$ points when exceeding category benchmark (e.g. $\ge 8g/100g$).
6. **Dietary Fibre ($g/100g$)**: Up to $+10$ points when exceeding benchmark ($\ge 4g/100g$).

---

## 3. Insufficient Data Rule
If **more than two** of the six core components (Energy, Sugar, Saturated Fat, Sodium, Protein, Fibre) are missing from the label, FoodLens strictly refuses to compute an arbitrary score and instead outputs:
- **Score:** `None`
- **Band:** `Insufficient data`
- **Reason:** *"Label lacks more than 2 core nutritional components required for a reliable score."*

---

## 4. Score Bands and Visual Colors
- **70–100:** *Nutritious & Balanced* (`#1B5E3F` Deep Green)
- **45–69:** *Moderate / Everyday* (`#F59E0B` Amber)
- **5–44:** *Consume Mindfully* (`#DC2626` Soft Red)

---

## 5. Regulatory Disclaimer
Every score result includes the following disclaimer:
> *"Educational prototype score based on category nutrient thresholds. Not an official FSSAI or medical diagnostic rating."*
