# FoodLens AI — Hindi & English Read-Aloud Audio Narration

## 1. Overview
The Read-Aloud module provides spoken audio summaries of nutritional facts, allergen alerts, and portion breakdowns in Hindi or English, specifically designed for visually impaired users, elderly family members, or consumers who find small label typography difficult to read.

## 2. Key Architectural Guarantees
1. **Zero LLM Translation for Numbers or Verdicts**:
   - Spoken scripts are built purely through deterministic string formatting from verified product JSON using `i18n/hi.json` and `i18n/en.json`.
   - The LLM is never permitted to calculate, round, or alter numbers.
2. **Strict Script Sequencing**:
   1. Allergen alert (MUST be spoken first whenever an allergen is present or uncertain).
   2. Product name & portion basis.
   3. Energy (Calories / किलोकैलोरी).
   4. Sugars & Teaspoons (चम्मच).
   5. In detailed mode: Protein, Total Fat, Sodium, notable flags.
   6. Mandatory closing disclaimer: *"Please verify on the pack. This is general information, not medical advice."*
3. **Banned Words & Safety**:
   - `safe`, `allergen-free`, `सुरक्षित`, `एलर्जी-मुक्त` are strictly forbidden.
   - Missing data is spoken as *"Not stated on label"* or *"लेबल पर जानकारी उपलब्ध नहीं"*.
4. **Speech-Friendly Conversions**:
   - Units are spelled out phonetically: `g` $\rightarrow$ "grams" / "ग्राम", `mg` $\rightarrow$ "milligrams" / "मिलीग्राम", `kcal` $\rightarrow$ "calories" / "किलोकैलोरी", `tsp` $\rightarrow$ "teaspoons" / "चम्मच".
5. **Length Constraints**:
   - Scripts are capped under 45 seconds (~90 words) in detailed mode and under 20 seconds (~40 words) in short mode.
6. **Privacy by Design**:
   - Narration scripts contain **zero personal names, avatars, or user identifiers**.
7. **Speech Provider Architecture**:
   - **BrowserSpeechProvider** (Default): Uses standard HTML5 `window.speechSynthesis` client-side. Zero server bandwidth, zero cloud API cost, 100% private. Alerts the user if a Hindi voice (`hi-IN`) is not installed on their device.
   - **ServerTTSProvider** (Optional): Cached synthesis by SHA-256 hash `hash(script + language + voice)`, enabled only when `ENABLE_SERVER_TTS=true`.
