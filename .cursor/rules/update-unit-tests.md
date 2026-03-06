---
description: Update unit tests to match pseudocode/specs and cover edge cases
globs:
  - "src/**/*.rs"
  - "tests/**/*.rs"
  - "benches/**/*.rs"
  - "docs/**/*.tex"
  - "Cargo.toml"
alwaysApply: false
---

# Update Unit Tests

Use this rule when pseudocode/specifications are updated, when adding/refactoring algorithms/functions, or when test coverage needs improvement.

## Process

### 1. Review current test coverage

- Read all relevant test files (unit, integration, inline tests).
- Identify which algorithms/functions are tested and note coverage gaps.

**Check against specifications:**
- Read pseudocode/spec docs (e.g., `docs/draft.tex`, `docs/pseudocode_*.tex`).
- List all algorithms defined in pseudocode.
- Map each algorithm to its implementation.
- Identify untested algorithms.

### 2. Identify gaps

- **Missing algorithm tests**: core algorithms without dedicated tests; helper functions not validated; edge cases not covered.
- **Missing type/shape validation**: input dimension checks; output shape verification; boundary conditions; invalid indices/params.
- **Missing mathematical property tests**: probability axioms (Σπ = 1, 0 ≤ π ≤ 1); identities (Q = r + β·V); bounds/monotonicity; numerical stability.
- **Missing integration tests**: multi-component interactions; end-to-end workflows; state transitions over time.

### 3. Create comprehensive tests

For each algorithm/function, include:
- **Correctness**: hand-computable examples when possible.
- **Properties**: monotonicity/bounds/identities/probability axioms.
- **Shape**: output dimensions match expectations.
- **Edge cases**: empty/single/terminal states.
- **Stability**: extreme values; assert finiteness (no NaN/Inf).

### 4. Naming conventions

Use descriptive test names that state the property/behavior being tested.

### 5. Validation checklist

- All pseudocode algorithms have tests.
- All public functions have tests.
- Input validation and output shape tests exist.
- Mathematical properties verified.
- Edge cases and numerical stability covered.
- Tests have descriptive names and helpful comments.
- All tests pass (and ideally no warnings).

### 6. Run and verify

Prefer running relevant subsets first, then the full suite (e.g., `cargo test`).
