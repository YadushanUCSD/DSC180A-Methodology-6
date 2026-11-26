# Decisions

One line per methodological decision: what you chose, why, and what it changed.
Agents append here via the `/new-feature` skill; you append here by hand.

- Exclude `casual`, `registered`: they sum to `cnt` exactly. Leaky model R^2 1.000 -> honest ridge 0.583.
- Exclude `cnt_2d_bfr`: a shipped 2-day lag we cannot test the alignment of. Build our own lags instead.
- Exclude `instant`, `yr`, `days_since_2011`: time indexes let a tree predict a flat constant past 2011 and a linear model extrapolate a trend we have no grounds for.
- Split 2011 / H1 2012 / H2 2012 by date. Test set touched once, after all feature work.
- Report mean and persistence baselines with every score. Persistence (test R^2 0.510, MAE 840) is within 0.07 R^2 of ridge and beats it on MAE; that caveat goes in the report.
- 2026-11-25: Keep the denylist (FORBIDDEN) rather than an allowlist: simpler to maintain with a small, fixed set of columns, and a silently dropped feature would only cost accuracy, which the baselines would reveal. Added test_leaky_columns_stay_forbidden, because removing "casual" from LEAKAGE_COLS previously passed every test.
- 2026-11-25: Kept the reference src/train.py over the agent's spec-written version (commit 600a3dd): its ridge was unstandardised and its baselines were not fit/predict objects, though all tests passed.
- 2026-11-25: Made data/raw/*.csv read-only (chmod -w); permission deny rules bind only the Edit/Write tools, not Bash.
- 2026-11-25: Added cnt_lag_2 (cnt two calendar days earlier; known at prediction time for date d). Validation R² ridge 0.6475 -> 0.6453 (-0.002), hgb 0.2185 -> 0.2481 (+0.030). Below the skill's 0.01 floor for ridge, so a null result; kept in code as the required Exercise 1 feature, not as a gain. The agent's first attempt (9129555) silently turned cnt_lag_7 into an 8-day lag by raising LAG_WARMUP and reported a false +0.027.
- 2026-11-25: Added ENCODED_COLS to src/config.py so every raw column is explicitly classified (forbidden, encoded/superseded, or feature), and test_every_raw_column_is_classified in tests/test_contract.py. Before it, six raw columns (mnth, holiday, weekday, workday, weather, season) were unclassified; a new column in the CSV now fails the suite instead of entering silently. Verified red by removing "season": "unclassified raw columns: ['season']".
- 2026-11-25: Wrote the seed-fault skill for the break/record/restore workflow repeated in Steps 4-7. It seeds and commits the broken state but never fixes, so fix turns are counted in a separate session.
- 2026-11-25: Added RAW_SHA256 and test_raw_data_is_unmodified. A Bash cp into data/raw/ bypassed the hook and the deny rules, and all 20 tests passed on altered data; chmod -w blocked it locally but does not survive a clone. The hash test fails the suite on any machine.
- 2026-11-25: Exercise 4: ratio target y = cnt / cnt_roll_7, behind `python -m src.train --target ratio` (writes reports/metrics_ratio.json; default pipeline and reports/metrics.json unchanged). Validation R²: hgb 0.2481 -> 0.7527, ridge 0.6453 -> 0.3905. Test consulted once, after this choice: hgb 0.6247 (MAE 831.2) vs raw ridge 0.5830 (MAE 945.5) and persistence 0.5099 (MAE 840.1); ridge ratio 0.0257. Judged defensible: cnt_roll_7 is shifted, so known at prediction time, and the ratio removes the trend that the 2011 ceiling made unlearnable for trees. But it was chosen after seeing HGB fail, and the valid->test drop (0.75 -> 0.62) shows some optimism. Committed metrics stay untransformed.
