---
description: Check consistency between narrative text and pseudocode in academic drafts
globs:
  - "docs/**/*.tex"
  - "docs/**/*.md"
alwaysApply: false
---

# Check Narrative–Pseudocode Consistency

Verify consistency between natural language descriptions (narratives) and algorithmic pseudocode in academic drafts so they describe the same procedure without contradictions.

## Checks

### 1. Identify mappings
- List all algorithms referenced in main text with locations.
- Extract narrative descriptions and corresponding pseudocode.
- Create mapping: Narrative section → Algorithm # → Algorithm name.

### 2. Variable and notation consistency
- Compare notation in narrative vs pseudocode.
- Ensure all variables mentioned in narrative appear in pseudocode and vice versa.
- Flag missing definitions and mismatches.

### 3. Procedure steps consistency
- Extract narrative steps and pseudocode steps.
- Check coverage (missing/extra steps) and order.

### 4. Input/output consistency
- Compare Require/Ensure/Return with narrative description.
- Flag mismatches.

### 5. Mathematical expression consistency
- Extract formulas from narrative and pseudocode.
- Check for sign/index/operator differences; flag contradictions.

### 6. Subroutine call consistency
- Ensure narrative mentions key subroutine dependencies.
- Verify algorithm references/labels are correct.

### 7. Terminology consistency
- Ensure the same concept uses the same term; flag confusing synonyms.

### 8. Edge cases / special conditions
- If narrative mentions special cases, ensure pseudocode includes them (and vice versa).

## Output format

Provide:
- mapping table
- per-algorithm issue lists (notation/steps/I-O/math)
- terminology table
- edge case coverage notes
- summary of critical vs minor issues and prioritized recommendations
