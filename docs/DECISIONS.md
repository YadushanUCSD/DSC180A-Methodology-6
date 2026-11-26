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

## 3. Leakage test and feature definition (Step 4)

- Already present in the starter: `FORBIDDEN` in src/config.py feeds both
  `feature_columns()` and tests/test_leakage.py.
- Verified the guard: replacing feature_columns() with `list(numeric)` makes
  test_no_forbidden_features fail.
- Gap found: removing "casual" from LEAKAGE_COLS passed every test, because
  builder and tests share the same definition. Agent added
  test_leaky_columns_stay_forbidden (asserts {casual, registered} ⊆ FORBIDDEN);
  verified it fails when "casual" is removed. Agent reported "8 passed"
  (one file only) and summarised rather than showing output; full suite: 15 passed.
- Denylist vs allowlist: kept the denylist. A new column is admitted
  silently rather than dropped silently. Reason: REASON

## 4. Feature contract (Step 5)

The starter already contains the finished src/features.py
(reindex_to_calendar, encode_weather with a loud failure, WEATHER_ORDER on
the mirror's labels, LAG_WARMUP = 7) and its tests. 728 raw rows -> 714
feature rows, matching the derived bound of 14. I did not have the agent
rewrite it. Instead I broke each fix on purpose and recorded what caught it.

- Calendar gap (2011-03-10): with reindex_to_calendar made a no-op, only
  test_calendar_is_complete_before_lagging failed (found a 2-day gap).
  test_lags_are_true_calendar_lags PASSED: it skips any row whose previous
  calendar day is missing, which is exactly the one wrong row (2011-03-11).
  The rolling-mean test checks only row 200. So the lag tests alone would not
  have caught this bug.
- Weather, UCI codes: encode_weather raised
  "unmapped weather labels: ['BAD', 'GOOD', 'MISTY']" (12 errors). Loud, as intended.
- Weather, silent mismatch (BAD renamed, guard disabled): no error anywhere
  except test_only_expected_rows_are_dropped: "lost 34 rows; expected at
  most 14". The 20 BAD days disappeared without a warning.

## 5. Training script and model comparison (Step 6)

Deleted src/train.py and had the agent write it from the spec (~2 hours,
many edit/retry cycles). Committed as-is (600a3dd), then restored the
reference version.

Agent's metrics (valid / test R²): mean −0.932 / −2.144, persistence
0.451 / 0.510, ridge 0.653 / 0.589, hgb 0.166 / −0.618.
Reference: mean −0.932 / −2.144, persistence 0.451 / 0.510,
ridge 0.648 / 0.583, hgb 0.219 / −0.498.

Correct: temporal split; persistence predicts cnt_lag_1 (no DummyRegressor
substitution); both baselines match the reference exactly.

Wrong, all with 15/15 tests passing:
- Ridge not standardised (plain Ridge(), no StandardScaler), against the spec.
- Baselines stored as dicts of lambdas, not objects with fit/predict;
  agent claimed otherwise. MODELS baselines are None until main() runs.
- HGB on default settings (reference: max_iter=300, random_state=0).
- Split dates hard-coded instead of read from TRAIN_END/VALID_END.
- metrics.json omits the feature list and split sizes.
Lesson: passing tests only cover what the tests check. "Objects with
fit/predict" and "standardised" were in the prompt but not in any test.

HGB range question: agent printed min/max per split (train max 6043; test
range 22–8714) and named Hurricane Sandy as the 22. When asked, it printed
the share above the 2011 max: valid 71/182 (39.0%), test 104/184 (56.5%).
Errors in its explanation: said ridge "stays closer to the mean" (it
extrapolates); called it overfitting; used 362 raw rows instead of the 348
the model trains on; did not address validation until asked.

Validation follow-up: agent wrote tmp_analysis.py despite "no files", then
looped ~90 min running it with `python -I` (cannot import src). Stopped it
and answered with my own script (MAE, in range vs above the 2011 max):

| model | split | in range | above ceiling | mean error above |
|---|---|---|---|---|
| hgb | valid | 830 | 2026 | −2026 |
| hgb | test | 1345 | 2455 | −2455 |
| ridge | valid | 671 | 1086 | −1060 |
| ridge | test | 954 | 941 | −918 |

- HGB under-predicts every above-ceiling day (MAE = |mean error|).
- The ceiling also drives much of HGB's weak validation score (39% of valid
  days above it, error 2026 vs 830), so it's not only small data and
  default settings, as the lesson suggests.
- Ridge's test error is the same in range and above it: it extrapolates.
- HGB is also worse in range on test than on valid, likely because the lag
  features are out of the training range too (not verified).

Ridge coefficients (standardised): cnt_roll_7 +567, cnt_lag_1 +362,
weather_severity −280, temp +200, windspeed −156, hum −117 (verified with
my own script against src/train.py). Lags lead, but weather terms are of
comparable size, so ridge learns "last week's level adjusted for today's
weather", not just "yesterday again". Better R² but worse MAE than
persistence means ridge fixes large misses on weather-change days (R²
squares errors) while being slightly worse on ordinary days.
Agent: right table, contradictory conclusion ("just yesterday again" and
"learning beyond persistence"), muddled R²/MAE explanation, misattributed
a quote to CLAUDE.md, and wrote tmp_ridge.py despite "no files" after six
failed commands.
