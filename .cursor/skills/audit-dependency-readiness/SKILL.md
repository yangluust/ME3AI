---
name: audit-dependency-readiness
description: Audits environment and dependency readiness for pipeline execution, including uv availability, dependency sync, import preflight, and first-failing-stage diagnosis. Use when output files are missing, scripts fail unexpectedly, or the user asks for dependency root-cause analysis.
---

# Audit Dependency Readiness

## Goal

Identify the first stage that fails due to missing dependencies or environment mismatch, and produce a concise root-cause report with command evidence.

## Workflow

1. Check toolchain availability:
   - `uv --version`
   - fallback: `python -m uv --version`
2. Validate environment provisioning:
   - `python -m uv sync` (if uv module exists)
3. Run import preflight in managed env:
   - `python -m uv run python -c "import pandas, openpyxl, matplotlib, scipy, tabulate"`
4. Execute pipeline stage-by-stage in order:
   - download
   - clean
   - adjust
   - inflation news
   - reputation
   - regression dataset
   - regressions
5. Stop at first hard failure and classify:
   - `missing-dependency`
   - `missing-upstream-artifact`
   - `config/path`
   - `data/content`
6. Verify artifact directories after run:
   - `input/`, `cleaned/`, `output/forecast_revision/`

## Command Sequence

From `data-pipeline/`:

```powershell
python -m uv --version
python -m uv sync
python -m uv run python -c "import pandas, openpyxl, matplotlib, scipy, tabulate"
python -m uv run python scripts/download_spf.py
python -m uv run python scripts/clean_spf.py
python -m uv run python scripts/adjust_spf_cpi10.py
python -m uv run python scripts/construct_spf_inflation_news.py
python -m uv run python scripts/construct_spf_reputation_measure.py
python -m uv run python scripts/construct_spf_regression_dataset.py
python -m uv run python scripts/run_spf_forecast_revision_regressions.py
```

## Report Format

- `First failing command`
- `Exact error` (single most informative traceback line)
- `Root cause` (dependency vs downstream missing file)
- `Cascade` (which later stages fail because of it)
- `Minimal fix` (no implementation unless asked)

## Rules

- No silent fallback recommendations.
- Do not suggest try/catch wrappers.
- Prioritize deterministic setup (`uv sync`, `uv run`).
- Treat missing generated files as downstream symptoms unless proven otherwise.

