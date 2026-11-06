# FoodLens AI — Limitations & Future Roadmap

## 1. Technical Limitations
1. **Curved & Glossy Packaging Reflections**:
   - Severe glare or cylindrical distortions on metallic chip packets or round bottles can degrade optical text recognition.
   - *Mitigation implemented:* Interactive review screen with amber low-confidence field alerts allowing immediate one-tap correction.
2. **Open Food Facts Coverage for Regional Brands**:
   - Tier-2/Tier-3 regional Indian packaged food items may not exist in Open Food Facts.
   - *Mitigation implemented:* Seamless fallback to OCR camera scanning and local persistent SQLite cache.
3. **Allergen Cross-Contamination**:
   - Label scanning only reads printed manufacturer statements; it cannot detect undeclared shared-equipment facility contamination.
   - *Mitigation implemented:* Clear banner wording: *"No allergen detected in the text we could read"*, never claiming *"allergen-free"*.
4. **Microbiological Safety & Expiry**:
   - FoodLens evaluates nutritional macro balance and ingredient roles; it does not measure expiry date, storage temperature, or microbiological spoilage.

## 2. Roadmap for Version 2 & Version 3
- [ ] **Mobile Camera Optimization (React Native / Flutter PWA)**: Direct WebAssembly barcode scanning and real-time bounding box overlay.
- [ ] **Full Multi-lingual OCR**: Expanded Hindi and regional Indian language OCR dictionary support for rural grocery labels.
- [ ] **Barcode Batch Comparison**: Scanning multiple items in grocery store aisles to automatically identify lower-sugar alternatives.

