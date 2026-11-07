# FoodLens AI — Family Profiles & Multi-Member Food Fit

## 1. Overview
The Family Profiles feature extends FoodLens AI's Personal Food Fit engine, enabling a single account to manage up to 8 household members (e.g. parents, children, grandparents) and evaluate any packaged food product for any combination of members simultaneously.

## 2. DPDP Act (2023) Compliance & Child Safety Guardrails
1. **Verifiable Parental Consent (Section 9, DPDP Act 2023)**:
   - When adding or managing a minor (age < 18), the account owner must explicitly confirm:
     *"I confirm I am the parent or lawful guardian of this child and consent to processing dietary preferences for food safety."*
2. **Pediatric Guidance Suppression**:
   - For all members under 18, caloric targets, weight-based goals, BMI metrics, and RDA reference intake guidance are strictly suppressed (`None`).
   - Only allergen warnings, ingredient disclosures, and general nutrition panel facts are shown, alongside an advisory to consult a pediatrician or registered dietitian.
3. **Data Erasure & Portability**:
   - Provides complete household data export in JSON format.
   - Deleting a household cascades to all attached member profiles, completely purging them from SQLite.

## 3. Severity Ranking & Allergen Matrix
When multiple family members are selected on the Result screen:
1. **Severity Invariant**:
   $$\text{CONTAINS\_YOUR\_ALLERGEN} > \text{MAY\_CONTAIN\_TRACES} > \text{UNKNOWN} > \text{NONE\_DETECTED\_IN\_READABLE\_TEXT}$$
   The top household alert banner always reflects the **worst status** among all selected members.
2. **Forbidden Phrasing**:
   - Never outputs *"Safe for everyone"*.
   - Uses: *"No selected allergens detected in readable text for the selected members. Verify on the pack."*
3. **Interactive Allergen Matrix**:
   - Grid rendering family members (rows) $\times$ selected allergens (columns) with color-coded status pills.

## 4. Dietary Preferences
Deterministic ingredient matching:
- **Vegetarian**: Green dot present; 0 meat, poultry, fish, gelatin, carmine.
- **Vegan**: Vegetarian rules + 0 dairy, honey, beeswax, shellac, lactose.
- **Jain**: Vegetarian rules + 0 root vegetables (onion, garlic, potato, radish, carrot).
- **Halal**: Free of pork and alcohol; returns `UNKNOWN` without an explicit halal certification mark.
