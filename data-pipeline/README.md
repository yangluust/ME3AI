# Data pipeline (SPF)

This package builds cleaned Survey of Professional Forecasters (SPF) tables, derived series (inflation news, reputation, regression inputs), and forecast-revision regression outputs. Configuration is JSON-driven under `config/`.

The canonical construction narrative lives in the repo root: `docs/source_of_truth/spf_dataset_construction.pdf` (and `.tex`).

## Layout

```
data-pipeline/
├── config/                 # JSON settings (paths, variables, sample window, x_definitions)
├── input/                  # Raw SPF downloads (Excel); tracked via .gitkeep when empty
├── cleaned/                # 3NF and derived CSVs (gitignored except .gitkeep)
├── output/                 # Analysis artifacts (e.g. regression tables, figures)
├── report/                 # codebook.qmd / codebook.html (+ Quarto support files)
├── src/
│   ├── spf_download.py     # SPF downloads
│   ├── spf_clean.py        # Individual microdata → 3NF CSVs
│   ├── spf_adjust.py       # CPI10 adjustment, inflation news, reputation, regression dataset
│   └── spf_regression.py   # Forecast-revision regressions and plots
├── scripts/
│   ├── download_spf.py
│   ├── clean_spf.py
│   ├── adjust_spf_cpi10.py
│   ├── construct_spf_inflation_news.py
│   ├── construct_spf_reputation_measure.py
│   ├── construct_spf_regression_dataset.py
│   └── run_spf_forecast_revision_regressions.py
└── tests/
```

## Config files

| File | Role |
|------|------|
| `config/spf_download.json` | SPF variables (e.g. CPI, CPI10), file types, `input/` output |
| `config/spf_clean.json` | `input_dir`, `cleaned_dir` for cleaning and downstream scripts |
| `config/forecast_revision.json` | Sample window, `x_definitions` (e.g. `raw_cpi10`, `adjusted_cpi10`) |
| `config/reputation_measure.json` | Parameters for reputation construction |

## SPF run order

Run from `data-pipeline/` (or pass absolute paths where scripts accept overrides):

1. `uv run python scripts/download_spf.py` — writes SPF files under `input/` per `spf_download.json`.
2. `uv run python scripts/clean_spf.py` — reads `input/Individual_*.xlsx`, writes `cleaned/forecast_individual.csv`, `cleaned/forecaster_survey.csv`.
3. `uv run python scripts/adjust_spf_cpi10.py` — writes `cleaned/adjusted_cpi10.csv`.
4. `uv run python scripts/construct_spf_inflation_news.py` — writes `cleaned/inflation_news.csv`.
5. `uv run python scripts/construct_spf_reputation_measure.py` — for each `x_definition`, writes under `cleaned/forecast_revision/<x_definition>/` (e.g. `reputation_measure.csv`).
6. `uv run python scripts/construct_spf_regression_dataset.py` — writes `cleaned/forecast_revision/<x_definition>/regression_dataset.csv`.
7. `uv run python scripts/run_spf_forecast_revision_regressions.py` — reads those datasets, writes `output/forecast_revision/<x_definition>/` (CSV, LaTeX, figures). The comparison workflow in this script expects `x_definitions` to include both raw and adjusted CPI10 sources as configured in `forecast_revision.json`.

## Codebook

Edit `report/codebook.qmd`, then render with Quarto, for example:

```bash
quarto render report/codebook.qmd
```

## Tests

```bash
uv run pytest tests/ -v
```

## Dependencies

See `pyproject.toml` (Python >= 3.10, pandas, openpyxl, matplotlib, scipy, tabulate, etc.). Dev group includes `pytest`.
