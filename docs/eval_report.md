# FoodLens AI — Evaluation and Quality Benchmark Report

**Date:** 5 November 2026  
**Test Suite:** 40 automated tests across unit, integration, property-based, and evaluation suites.  
**Result:** 40 / 40 Passed (100% pass rate in 7.93s).

---

## 1. Quality Metrics Summary

| Layer | Benchmark / Test Scope | Metric Measured | Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Barcode Engine** | EAN-13 Checksum calculation, UPC-A conversion, India (890) detection | Accuracy / Valid check digit match | **100%** | PASS |
| **Calculator Engine** | Property-based tests via Hypothesis ($100$ iterations) | Scaling linearity, $100g$ identity, None preservation | **100%** | PASS |
| **Validation Rules** | Seeded corruption (sugars > carbs, sat fat > fat, protein > 100g) | Detection rate of invalid records | **100%** ($3/3$) | PASS |
| **Parser Engine** | Real-world label fixtures (comma decimals, multi-lingual, kJ vs kcal) | Extraction & unit normalization | **100%** | PASS |
| **Scoring Engine** | Known reference categories (biscuits, cereals, snacks, drinks) | Insufficient data refusal & category sensitivity | **100%** | PASS |
| **AI Advisor** | Grounding verification against input JSON payload | Zero hallucinated numbers ($0$ flagged) | **100%** Grounded | PASS |
| **Quest Gamification** | Daily XP caps, per-product caps, protective streak freezes | Cap enforcement & streak recovery | **100%** | PASS |
| **REST API** | End-to-end route handling with SQLite persistence | HTTP status code and response payload integrity | **100%** ($4/4$) | PASS |

---

## 2. Real-World Product Evaluation Set
Evaluated across 20 popular packaged foods in India (`data/sample_products.csv`):
- **Biscuits & Cookies:** Parle-G, Britannia Good Day, Sunfeast Dark Fantasy, Monaco
- **Instant Foods:** Maggi 2-Minute Masala Noodles, Knorr Tomato Soup
- **Savory / Namkeen:** Haldiram's Aloo Bhujia, Lay's Magic Masala, Kurkure Masala Munch
- **Dairy & Spreads:** Amul Butter, Epigamia Greek Yogurt, Dabur Pure Honey
- **Beverages:** Frooti Mango Drink, Tata Tea Premium, Nescafe Classic
- **Breakfast Cereals & Oils:** Kellogg's Corn Flakes, Saffola Gold Oil
- **Chocolates & Confectionery:** Cadbury Dairy Milk, Nestle KitKat, Moong Dal Halwa

All 20 products completed validation, portion scaling (serving and packet portions), sugar teaspoon conversion, and category-aware scoring with 0 exceptions.
