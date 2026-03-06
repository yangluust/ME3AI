---
description: Review and improve academic draft text (notation, flow, tone, math consistency)
globs:
  - "docs/**/*.tex"
  - "docs/**/*.md"
  - "docs/**/*.bib"
alwaysApply: false
---

# Improve Draft Description

Review and improve academic draft text by checking notation definitions, logical flow, tone, and mathematical consistency.

## Instructions

When invoked on draft text, perform these checks:

### 1. Notation and concept definitions
- List **all** notations/symbols/technical concepts used.
- Verify each is defined at its **first** appearance.
- Flag undefined or late-defined terms.

### 2. Paragraph and sentence structure
- Each paragraph has a clear topic/purpose.
- Sentences are concise; flag overly complex sentences.
- Remove redundancy and fix ambiguous references.

### 3. Logic flow
- Arguments progress clearly; conclusions follow from premises.
- Identify logical gaps/unexplained jumps; improve transitions.

### 4. Academic tone
- Flag informal/colloquial language.
- Ensure consistent voice; use appropriate hedging.

### 5. Grammar, spelling, and punctuation
- Fix spelling/grammar/collocation/punctuation.
- **Remove all em dashes (—) and en dashes (–) from main text**; replace with parentheses/colons/semicolons or split sentences.

### 6. Mathematical consistency
- List all equations/formulas.
- Verify notation is consistent across math and matches the narrative.
- Flag contradictions.

### 7. Proof consistency and validity
- For each theorem/lemma/proposition proof, verify logical validity, completeness, assumption tracking, case coverage, and correct application of definitions/results.
- Flag circular reasoning, missing cases, unjustified steps, direction/quantifier errors, ambiguity.

## Output format

Produce:
- tables for notation/concepts and math consistency
- bullet lists of structure/logic/tone/grammar issues with locations
- a revised cleaned draft
