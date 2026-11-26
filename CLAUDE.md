# Bikeshare demand capstone

Daily Capital Bikeshare counts, 2011-2012. We forecast `cnt` (total daily
rides) from calendar, weather, and lagged-demand features.

## Commands
- `make data` - download raw CSV and assert its shape
- `make features` - build `data/processed/features.parquet`
- `make train` - fit models, write `reports/metrics.json`
- `make test` - pytest; run this before claiming anything works
- `make all` - the three pipeline stages in order
- `python -m src.train --target ratio` - exploratory ratio target
  (Exercise 4), writes `reports/metrics_ratio.json`. `reports/metrics.json`
  is always the untransformed pipeline; never commit ratio numbers into it.

## Non-negotiable rules
- **Never** put `casual` or `registered` in a feature set:
  `casual + registered == cnt` exactly. `src/config.py` lists these and the
  other excluded columns (`cnt_2d_bfr`, raw time indexes) with the reason
  for each. Derive feature lists from `FORBIDDEN`; never hand-type them.
- **Never** split this data randomly. Use `src.train.temporal_split`.
  Train = 2011, valid = H1 2012, test = H2 2012. Never tune on test.
- Any new lag or rolling feature must be built on a gap-free calendar
  index (`src.features.reindex_to_calendar`) and must `.shift(1)` before
  it aggregates. Add a test for it in `tests/test_leakage.py`.
- Report the mean baseline **and** the persistence baseline (yesterday's
  count) alongside every model. A negative R^2 is a finding, not a bug
  to hide.
- Every raw column must be classified in `src/config.py` (`FORBIDDEN` or
  `ENCODED_COLS`) or be a feature; `tests/test_contract.py` fails otherwise.
- **Never** write to `data/raw/` by any route, including Bash `cp`/`mv`.
  Its sha256 is tested (`RAW_SHA256`).
- `cnt_lag_7` and `cnt_roll_7` are built from `LAG_WARMUP`. Raise it only
  for a feature needing more than 7 days of history, never to fix a test.

## Skills
- `/new-feature <name>` - add a feature, test first, report validation delta.
- `/seed-fault <description>` - seed one fault, record red output and hook
  stderr in `docs/SEEDED_FAULTS.md`, commit the broken state. Never fixes.

## Style
- Standard library, pandas, scikit-learn only. No new dependencies
  without asking. Versions are pinned in `requirements.txt`.
- Modules are runnable: `python -m src.<module>` prints a one-line `OK ...`
  summary.
- Paths and constants live in `src/config.py`. Nothing is hardcoded twice.

## Gotchas
- The mirror in `DATA_URL` is missing 2011-03-10. It is NOT the UCI file:
  728 rows from 2011-01-03, not 731 from 2011-01-01.
- `weather` uses the labels `GOOD` / `MISTY` / `BAD`, not the UCI codes 1-4.
- Ridership grew ~65% from 2011 to 2012, so tree models trained on 2011
  cannot extrapolate to 2012. That is the headline result, not an error.
- 2012-10-29 (Hurricane Sandy, 22 rides) is in the test set. Expect it in
  any residual plot.
