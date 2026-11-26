**Decisions**:

-Excluded casual and registered because their sum equals cnt identically. Dropping them changed a leaky R² of 1.000 to an honest Ridge R² of 0.583.

-Excluded cnt_2d_bfr since it is a pre-computed two-day lag and the alignment cannot be verified. I construct lags directly from the data.

-Excluded instant, yr, and days_since_2011 because time indexes let trees output a flat constant after 2011 and make linear models extrapolate unsupported trends.

-Split the dataset chronologically into 2011 (training), H1 2012 (validation), and H2 2012 (test), touching the test set only once after completing feature work.

-Reported both mean and persistence baselines alongside every model score. Persistence achieves a test R² of 0.510 and MAE of 840—within 0.07 R² of Ridge while beating it on MAE.

-Kept the FORBIDDEN denylist rather than using an allowlist because a small, fixed set of forbidden columns is easier to maintain, and any silently dropped feature would hurt accuracy in ways the baselines would catch. Added test_leaky_columns_stay_forbidden after realizing that deleting "casual" from LEAKAGE_COLS previously still passed all tests.

-Kept the reference src/train.py rather than the agent's spec-generated version (commit 600a3dd), which left Ridge unstandardized and implemented baselines as ad-hoc logic instead of fit/predict objects despite passing the test suite.

-Marked data/raw/*.csv read-only with chmod -w because permission deny rules only restrict Edit and Write tools, not Bash commands.

-Added cnt_lag_2 (the count from two calendar days prior, known at prediction time for date d). Validation R² moved from 0.6475 to 0.6453 (-0.002) for Ridge and from 0.2185 to 0.2481 (+0.030) for HGB; because Ridge fell short of the skill's 0.01 gain floor, I treat it as a null result retained solely to satisfy Exercise 1. The agent's initial attempt (9129555) raised LAG_WARMUP, turning cnt_lag_7 into an eight-day lag and reporting a misleading +0.027 gain.

-Added ENCODED_COLS to src/config.py and test_every_raw_column_is_classified to tests/test_contract.py so every raw column must be explicitly categorized (forbidden, encoded/superseded, or feature). Previously, six raw columns (mnth, holiday, weekday, workday, weather, and season) were unclassified; now any new column in the CSV fails the test suite instead of slipping in unnoticed, which I confirmed by removing "season" and seeing unclassified raw columns: ['season'].

-Created the seed-fault skill to standardize the break, record, and restore cycle used across Steps 4–7. It seeds and commits broken states without fixing them so repair turns are tracked in separate sessions.

-Added RAW_SHA256 and test_raw_data_is_unmodified after a Bash cp into data/raw/ bypassed both hooks and tool deny rules while all 20 tests still passed on modified data. While chmod -w prevents accidental local edits, it does not carry over across clones, whereas the hash check fails the suite on any machine.

-Implemented the ratio target y = cnt / cnt_roll_7 for Exercise 4 behind python -m src.train target ratio (writing to reports/metrics_ratio.json while keeping the default pipeline and reports/metrics.json unchanged). Validation R² shifted from 0.2481 to 0.7527 for HGB and from 0.6453 to 0.3905 for Ridge; evaluating the test set once afterward gave HGB an R² of 0.6247 (MAE 831.2) against raw Ridge at 0.5830 (MAE 945.5) and persistence at 0.5099 (MAE 840.1), while ratio Ridge dropped to 0.0257. Although defensible because cnt_roll_7 is shifted prior to aggregation and removes the trend that made the 2011 ceiling hard for trees, I adopted it after seeing HGB struggle on validation and noted some validation optimism in the 0.75 to 0.62 test drop, leaving committed metrics untransformed.

-Expanded CLAUDE.md from 41 to roughly 55 lines to document both skills, require column classification, extend the no-writes rule on data/raw to Bash (addressing fault 4), warn against raising LAG_WARMUP after the broken cnt_lag_7 attempt, and label --target ratio as exploratory so metrics.json stays untransformed.

-Switched from qwen3.5:9b (running locally via Ollama on an M2 MacBook with 16 GB RAM at 5–15 minutes per turn) to Claude Sonnet (claude-sonnet-5-5 in Claude Code with a Claude Pro login) starting at seeded fault 1 for the Part 5 deliverables.
