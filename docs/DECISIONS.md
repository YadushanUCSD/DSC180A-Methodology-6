# Decisions

## 1. Data characterisation (Step 2, plan mode, bikeshare-coder / qwen3.5:9b)

The agent answered from `src/config.py` only and did not inspect the CSV.
Each fact below was verified by hand with pandas.

| Fact | Verified value | Agent |
|---|---|---|
| Rows / date range | 728, 2011-01-03 to 2012-12-31 | Not reported |
| Missing calendar day | 2011-03-10 | Not reported |
| Weather labels | GOOD 463 / MISTY 245 / BAD 20 (text, not codes 1–4) | Not reported |
| Leakage | `casual`, `registered`: `casual + registered == cnt` on every row | Correct |
| `cnt` | The target | Wrongly listed as a "leakage" column |
| `cnt_2d_bfr` | Two-day lag; known at prediction time; excluded because its alignment is unverified | Correct (unverified, not leakage) |
| Random split | Trains on future days; hides the ~65% growth; lags leak across neighbouring days | Partly garbled |

Decision: use `src/config.py`'s three exclusion sets (leakage, time index,
unverified) as written, and `src.train.temporal_split` for all evaluation.

## 2. Naive model (Step 3, bikeshare-coder / qwen3.5:9b)

- Prompt: "Build a model to predict cnt from the other columns. Report R-squared."
- Agent ran the existing `src.train` pipeline (temporal split, leak-free
  features) instead of building a naive model. CLAUDE.md at the time was a
  short version without the Commands section. Reported test R²: mean −2.14,
  persistence 0.51, ridge 0.58, HGB −0.50 (matches the expected chart).
- Agent made and reverted unrequested edits to `src/config.py` and
  `src/train.py` (parquet → CSV → parquet). Net diff: none.
- Agent attributed the HGB failure to "overfitting". The actual cause is that
  trees cannot extrapolate beyond the 2011 maximum, which 56% of test days exceed.
- The leakage hook failed on every edit (`No module named pytest`), so it was
  not actually guarding anything. Fixed by installing requirements.
- `python -m src.leakage_demo`: features [casual, registered, temp, hum],
  test R² = 1.000000.
- lstsq cnt ~ casual + registered: coef [1, 1], max abs residual 2.7e-12
  (floating-point error). Computed by me. Agent reproduced it when told to
  run lstsq: it ran the command and printed coef [1, 1], intercept ≈ 0,
  max residual 8.6e-12.
