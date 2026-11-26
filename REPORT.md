# Forecasting daily bikeshare demand: what the agent built, and what I verified

## Results

The data uses a temporal split where 2011 is for training (the first half of 2012 for validation (182 rows)), and the second half of 2012 is for testing (184 rows). In the table, "before" refers to the starter pipeline with 14 features, and "after" includes my Exercise 1 feature, `cnt_lag_2` which brins the total to 15 features. The "after" numbers are from `reports/metrics.json`, which can be reproduced identically by running `make all` on a fresh clone.

| Model | Pipeline | Valid R² | Valid MAE | Test R² | Test MAE |
|---|---|---|---|---|---|
| baseline_mean | before | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| baseline_mean | after | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| baseline_persistence | before | 0.4507 | 900.6 | 0.5099 | 840.1 |
| baseline_persistence | after | 0.4507 | 900.6 | 0.5099 | 840.1 |
| ridge | before | 0.6475 | 832.9 | 0.5833 | 947.1 |
| ridge | after | 0.6453 | 833.4 | 0.583 | 945.5 |
| hgb | before | 0.2185 | 1296.6 | -0.4975 | 1972.6 |
| hgb | after | 0.2481 | 1269.8 | -0.4737 | 1947.9 |

Because the baseline models do not rely on features, their scores remain unchanged before and after adding `cnt_lag_2`.

**Audit of this repository.** When I ran `agent/audit.py` it returned `leakage: none` and confirmed that `temporal_ok`, `baseline_reported`, and `reproducible` are all true. Two minor issues were flagged. They do not affect the metrics. They only the HGB model sets a random seed (the others are already deterministic), and `make data` skips verifying the raw file's hash, leaving that check to `make test` (`test_raw_data_is_unmodified`). The audit did miss that `casual + registered == cnt` holds in the raw dataset. "None" is accurate for the pipeline. However, a more thorough audit would have see that this identity exists and would be properly excluded.

## Headline finding

A naive evaluation produces an invalid R² of 1.000 because `casual + registered` reconstructs `cnt` with a maximum least-squares residual of just 2.7e-12 (`python -m src.leakage_demo`). With a proper temporal split, the mean baseline drops into negative territory on the test set (R² -2.144) because ridership grew by around 65%, making the 2011 average far too low for late 2012. Ridge regression achieves a test R² of 0.583 compared to the score of 0.510 on the persistence baseline. This is an improvement, but it loses to persistence on MAE (945.5 vs. 840.1 rides). Gradient boosting (HGB) scores -0.474 on the test set. This beats the mean baseline, but it remains negative because decision trees cannot extrapolate beyond the maximum value seen during training. Since 104 of the 184 test days (56.5%) exceed the 2011 peak of 6,043 rides, HGB under-predicts every single one of them, resulting in an MAE of 2,455 rides (equal to the absolute mean error) above that ceiling. Adding my `cnt_lag_2` feature shifted Ridge's validation R² by -0.002 (from 0.6475 to 0.6453), which made it fall short of the 0.01 threshold. It is a null result, which is kept in the codebase solely to satisfy the Exercise 1 requirement.

## Exercise 4: target transformation

Tree-based models struggle here because demand in 2012 outgrows the 2011 training range. Because of this, I removed the raw demand level from the target by predicting the ratio `y = cnt / cnt_roll_7` and then multiplied the predictions back by `cnt_roll_7`. Because this ratio stays centered near 1.0 across both years, the tree never has to extrapolate. This behavior is controlled via a flag (`python -m src.train --target ratio`, which outputs `reports/metrics_ratio.json`), and leaves the committed `reports/metrics.json` untouched.

On the validation set, this transformation boosted HGB's R² from 0.2481 to 0.7527 (with an MAE of 677.9), outperforming raw Ridge's 0.6453, while causing Ridge itself to drop from 0.6453 to 0.3905. I verified the agent's implementation using a script that reproduced both validation numbers exactly. Then, I evaluated on the test set once. The ratio-target HGB achieved an R² of 0.6247 (MAE 831.2), which beat raw Ridge's 0.583 (MAE 945.5) and persistence's 0.5099 (MAE 840.1). The ratio-target Ridge collapsed to 0.0257.

I think this approach is defensible. Because `cnt_roll_7` is shifted before aggregation, it is known at prediction time and introduces no data leakage, and predicting relative to a recent moving average is a standard way to handle trend. However, I only introduced this transformation after seeing HGB fail on the 182 validation days, and the drop from validation to test (0.75 down to 0.62) suggests that part of the validation gain was optimistic. On test, its MAE beats persistence by only 9 rides per day. The exact same transformation ruins Ridge, proving that which model is better depends heavily on how the target is framed and showing that the comparison in the Results table is not model-neutral.

## Exercise 5: ridge vs persistence

Based on the current evidence, Ridge regression is not worth deploying over a simple persistence model. On the test set, Ridge improves R² by 0.073 (0.583 vs. 0.510), but its MAE is worse by 105 rides per day (945.5 vs. 840.1). This means that persistence is actually more accurate on a typical day. Ridge's higher R² comes from avoiding massive errors, since R² squares residuals. Looking at Ridge's standardized coefficients, weather variables carry nearly as much weight as the lag features (`weather_severity` -280, `temp` +200, `windspeed` -156, and `hum` -117, compared to `cnt_roll_7` +567 and `cnt_lag_1` +362). This allows Ridge to adjust when the weather shifts abruptly and yesterday becomes a poor predictor. This only matters if large misses are disproportionately costly, such as running completely out of bikes on an unexpectedly warm day. The evidence across periods is inconsistent because on validation, Ridge outperforms persistence on both R² (0.6453 vs. 0.4507) and MAE (833.4 vs. 900.6), meaning the MAE ranking reverses between the two halves of 2012. Because of this, I would keep persistence as the production default and treat Ridge as a specialized candidate for days with sharp weather changes.

## Attribution

Model: qwen3.5:9b via Ollama (64k context) on an M2 MacBook with 16 GB, for the tutorial steps and the first attempts at Steps 3, 6 and 8. I switched to Claude Sonnet (claude-sonnet-5-5, via Claude Code with a Claude Pro login) for part 5, because local turns took 5-15 minutes and single tasks took up to two hours. I also used Claude in the claude.ai chat interface throughout as a guide; it drafted many commands, tests and much of the wording here, which I ran, checked and edited.

**Generated by an agent or assistant**
- The initial agent version of `src/train.py` (qwen3.5:9b, commit 600a3dd), which I later replaced with the reference implementation.
- The first attempt at `cnt_lag_2` and `test_cnt_lag_2_is_true_two_day_lags` (qwen3.5:9b, commit 9129555), which inadvertently shifted `cnt_lag_7` into an 8-day lag and had to be fixed manually.
- `test_leaky_columns_stay_forbidden`: code supplied by the chat assistant, appended to the file by qwen3.5:9b.
- Seeded faults 1–3 and their corresponding fixes (Claude Sonnet, via `/seed-fault`; each fix took 3 turns), which included `test_encode_weather_rejects_unmapped_label`.
- The `--target ratio` flag in `src/train.py` and `METRICS_RATIO` in `src/config.py` (Claude Sonnet).
- Several items drafted by the chat assistant: `test_cnt_lag_2_on_named_date`, `ENCODED_COLS` along with the unclassified-column tests, `RAW_SHA256` and `test_raw_data_is_unmodified`, `.claude/skills/seed-fault/SKILL.md`, the additions to `CLAUDE.md`, verification scripts, and the initial draft of this report.
- `reports/audit.jsonl` (`agent/audit.py`, Claude Sonnet) and the teammate audit in `docs/AUDIT.md` (leakage-auditor subagent, Claude Sonnet).

**My Decisions** (each documented with a line in `docs/DECISIONS.md`)
- I confirmed the `casual`/`registered` identity via residual checks, excluded `cnt_2d_bfr` because it was unverified rather than leaky and locked down the leaky columns with a test.
- Enforcing strict schema validation so every raw column must be classified in `ENCODED_COLS`.
- I kept the temporal split and both baseline models while rejecting the agent's initial `train.py`.
- Protecting raw data immutability across all workflows using `chmod -w` locally and hash verification in the test suite.
- I rejected the agent's claimed "+0.027" gain for `cnt_lag_2` after discovering it came from a broken `cnt_lag_7`, documented the feature as a null result.
- I selected the ratio target transformation, evaluated its caveats, and restricted myself to a single test-set evaluation.
- Switching the agent model from qwen3.5:9b to Claude Sonnet, and stating it here.
