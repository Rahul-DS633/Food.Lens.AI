# FoodLens AI — Report Inaccurate Data & Admin Review Queue

## 1. Overview
The Data Reporting & Verification module empowers consumers and guests to submit corrections for inaccurate label facts, serving sizes, ingredients, or allergen notices, while providing administrators with a secure, audit-trailed workflow to verify and publish corrections.

## 2. Key Architecture & Principles
1. **Append-Only Revisions**:
   - Original label OCR data and scans are never deleted or overwritten.
   - Verified changes are recorded in `product_revisions` tracking `old_value`, `new_value`, `source`, `report_id`, `changed_by`, and `changed_at`.
2. **Deterministic Auto-Checks (`foodlens/report_checks.py`)**:
   - Validates plausibility (non-negative, $\le 100\text{g}$ per $100\text{g}$).
   - Verifies subset invariants:
     $$\text{added sugar} \le \text{total sugar} \le \text{carbs}$$
     $$\text{saturated fat} \le \text{total fat}$$
   - Compares attached photo evidence via OCR fuzzy matching.
   - Detects duplicate submissions on the same product field and computes consensus priority scores.
   - *Safety invariant*: Auto-checks only advise. Nothing is published without human admin review.
3. **Security & Privacy Safeguards (`foodlens/image_security.py`)**:
   - Re-encodes uploaded evidence photos through PIL to strip all EXIF, GPS coordinates, and camera metadata.
   - Maximum upload size: 8 MB.
   - Stores photos outside web root in `data/uploads/evidence/`.
   - Rate limits submissions by hashed IP/session.
   - Requires explicit privacy agreement: *"I confirm I am not sharing personal information in this report."*

## 3. Database Schema
- `data_reports`: id, product_id, field, current_value, proposed_value, evidence_image_path, comment, reporter_hash, status (pending, approved, rejected, needs_info, duplicate), priority_score, auto_checks_json, created_at, reviewed_by, reviewed_at, reviewer_note.
- `product_revisions`: id, product_id, field, old_value, new_value, source, report_id, changed_by, changed_at.

## 4. Admin Review Workflow (`app/pages/9_Admin.py`)
- Protected by `FOODLENS_ADMIN_PASSWORD_HASH`.
- Metrics panel: total reports, pending count, approved count, rejected count, approval rate (%).
- Filtering by status and field.
- Actions:
  - **Approve**: Writes `product_revisions`, updates `products`/`nutrition` in place, sets `verification_status = "admin_verified"`.
  - **Reject**: Records reviewer reason.
  - **Needs Info** / **Mark Duplicate**.
