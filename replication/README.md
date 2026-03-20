# Figure Replication

This folder reproduces the single figure saved in `plotsave_Jan2025` from the raw SPF Excel files:

- `Individual_CPI.xlsx`
- `Individual_CPI10.xlsx`

## Workflow

1. Read `Individual_CPI.xlsx` and rebuild the short-horizon quarterly revision table used by the figure:
   - all-member levels and quantiles
   - continuing-member levels and quantiles
   - all-member revisions
   - continuing-member revisions (`FRCmn`)
2. Read `Individual_CPI10.xlsx` and rebuild the long-term expectations table used by the figure:
   - mean, trimmed mean, median, quantiles
   - quarter-to-quarter mean change
   - current-script `CPI10Cmn` / `CPI10Cmd` / `CPI10Cmntr`
   - continuing-member change measures
3. Merge `FRCmn` with the long-term expectations table on quarter.
4. Recreate the back-of-the-envelope reputation measure from `CPI10Cmn`.
5. Build `FR0shift` and `FR0shift_2`.
6. Estimate the three figure regressions:
   - `dCPI10mn ~ FR0`
   - `dCPI10mn ~ FR0shift`
   - `dCPI10mn ~ FR0shift_2`
7. Cumulate actual and fitted changes and save the replicated figure.

## Saved Outputs

- `intermediate/cpiall_levels_all.csv`
- `intermediate/cpiall_levels_continuing.csv`
- `intermediate/cpiall_revisions_all.csv`
- `intermediate/cpiall_revisions_continuing.csv`
- `intermediate/lte.csv`
- `intermediate/model_input.csv`
- `intermediate/model_coefficients.csv`
- `intermediate/fitted_changes.csv`
- `intermediate/cumulative_series.csv`
- `figures/CPI10Y_cumuchange.jpg`
- `figures/CPI10Y_cumuchange.png`

## Important Note

The current MATLAB code and the narrative docs are not fully aligned. In `CPI_LT_data_overview2.m`, the variables saved as `CPI10Cmn`, `CPI10Cmd`, and `CPI10Cmntr` are computed from all current respondents in each quarter, not from a matched continuing-member sample. This replication script follows the MATLAB code as written so that the figure behavior is preserved.

The saved Python figure reproduces the line construction and model fit logic. It does not recreate MATLAB's `recessionplot` shading, because the recession-date source is not documented in the raw-input workflow.
