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
