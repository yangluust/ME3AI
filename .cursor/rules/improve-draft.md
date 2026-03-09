---
description: Review and improve academic draft text (notation, flow, tone, math consistency, line length)
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

### 8. Line length and text width (source and typeset)
- **Source:** Keep lines in the source file within a reasonable length (e.g., 80 to 100 characters) so that the compiled PDF has proper line breaking.
- **Typeset:** Ensure the compiled output does not have text stretching to the margin (no overfull hbox or single long lines to the margin).
- **LaTeX prose:** Break long paragraphs into shorter lines in the source; rephrase if needed so that no paragraph or caption produces overfull/underfull hbox or stretched lines.
- **LaTeX itemize/enumerate:** When an item’s label plus content would form one long line to the margin, insert `\\` after the label (e.g., after the colon following a bold heading) so the description starts on the next line and wraps within the margin.
- **LaTeX tables:** Break long table cells into two rows (e.g., definition on first row, continuation or examples on the next) or rephrase so that cell content fits.
- **LaTeX URLs:** Use a package that allows URL line breaks (e.g., `\usepackage{xurl}`) when the document contains long URLs. In prose, use `\url{...}` (not `\texttt{...}`) for URLs so they can break; `\texttt` does not allow breaks and causes overfull lines.
- **LaTeX algorithms:** When a `\State` line (e.g., a long \textbf{Require} or a long statement) would extend to the margin, split it: put the first part in `\State` and the continuation on the next line with `\Statex \quad ...` so the content spans two lines without adding an extra line number.

## Output format

Produce:
- tables for notation/concepts and math consistency
- bullet lists of structure/logic/tone/grammar issues with locations
- a revised cleaned draft
