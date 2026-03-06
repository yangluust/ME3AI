---
description: Post-implementation verification checklist (pseudocode consistency, pipeline flow, DRY, no legacy)
globs:
  - "src/**/*"
  - "tests/**/*"
  - "scripts/**/*"
  - "docs/**/*"
  - "Cargo.toml"
alwaysApply: false
---

# Post-Implementation Update Checklist

Perform comprehensive post-implementation verification and report findings clearly.

## 1. Pseudocode consistency check
- Locate relevant pseudocode/specs (docs/, comments, issues).
- Compare every function/method against its pseudocode counterpart:
  - structure matches (loops/conditionals/order)
  - variable names correspond to notation
  - formulas implemented exactly
  - no improvised logic
- Report discrepancies with file:line references.

## 2. Pipeline value flow check
- Trace data flow end-to-end.
- Verify input shapes/types at each stage; no silent conversions/data loss; outputs match downstream expectations; config propagates correctly.
- Report breaks/mismatches with file:line references.

## 3. DRY principle check
- Grep for hardcoded constants (LR/dimensions/paths); ensure params come from config; config saved with outputs.
- Identify duplicated logic; prefer shared utilities.
- Report each violation with file:line and suggested fix.

## 4. Streamlined-to-latest check (no legacy)
- Search for backward-compat patterns (version/legacy/deprecated fallbacks; multiple code paths old vs new).
- No unused parameters kept “for compatibility”.
- Implementation matches latest pseudocode only.
- Report each legacy artifact with file:line and **DELETE THIS** recommendation.

## Report format

Use:
- Pass/Issues for each section
- Bullet list of issues with file:line
- Summary totals and readiness assessment

If you cannot verify something, say **UNABLE TO VERIFY** with the reason.
