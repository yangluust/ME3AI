---
name: audit-worktree-paths
description: Audits a repository for hardcoded absolute paths and verifies worktree-relative path conventions in runtime code and TeX/docs. Use when the user asks to check path hardcoding, path portability, output path issues, or worktree-relative path policy.
---

# Audit Worktree Paths

## Goal

Detect path portability issues and report whether runtime outputs are resolved from worktree-relative config, not machine-specific absolute paths.

## Scope

- Runtime code first (`scripts/`, `src/`, config files).
- TeX/doc path macros second (`docs/source_of_truth/*.tex`).
- Documentation/examples last (lower severity than runtime issues).

## Audit Checklist

1. Search for absolute-drive patterns in code/docs:
   - `C:\`, `D:\`, `/Users/`, `/home/`, `/mnt/`
2. Search for output path literals:
   - `output/forecast_revision`, `output/`, `cleaned/`, `input/`
3. Classify each finding:
   - `runtime-hardcoded` (must fix)
   - `runtime-config-driven` (ok)
   - `doc-only` (informational)
4. Verify output root policy:
   - one config key for output root (worktree-relative)
   - runtime resolves via worktree root + relative config value
5. Verify TeX uses a single macro root for output artifacts.

## Command Pattern

Run from repo root:

```powershell
rg "d:/|c:/|[A-Za-z]:\\\\|/Users/|/home/|/mnt/" -g "*.{py,tex,json,md,qmd,yml,yaml,toml}"
rg "output/forecast_revision|output\\\\forecast_revision|output/|cleaned/|input/" .
```

Then inspect key files:

- `data-pipeline/config/forecast_revision.json`
- `data-pipeline/scripts/run_spf_forecast_revision_regressions.py`
- `docs/source_of_truth/spf_dataset_construction.tex`

## Report Format

- `Root cause`: one-line statement.
- `Evidence`: 3-8 bullets with file paths and exact path expressions.
- `Impact`: what breaks (portability, compile, output discovery).
- `Action`: minimal changes needed (do not implement unless asked).

## Severity Rules

- High: absolute path in runtime write/read logic.
- Medium: split output roots between config and literals.
- Low: doc-only literals that do not affect execution.

