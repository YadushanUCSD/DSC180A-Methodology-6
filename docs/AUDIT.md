# Audit of a teammate's repository (Exercise 3)

**Repository audited:** https://github.com/aceyq/bikeshare-open.git (HEAD 1082e07; starter commit f78104c)

**How it was run:** the leakage-auditor subagent was run from my own repo's Claude Code with my teammate's clone added as a read-only working directory.

## Auditor output (verbatim)

> All five checks pass for git diff f78104c HEAD -- src tests (HEAD 1082e07): perturbing same-day or later target values changed none of the 15 features, all lag and rolling values matched calendar-day recomputation, the split is by date with the scaler fit on the 348 training rows only, the 14 dropped rows are exactly the warm-up and gap rows within the tested bound, and both baselines are in every metrics JSON the code writes (23 tests passed, and reports/metrics.json and both hgb_delta JSONs reproduced identically).
>
> As required for runs that write files, I ran the tests and pipeline on a copy at /private/tmp/claude-501/-Users-yadi-Downloads-bikeshare-open-starter/f32308e6-e105-450f-8c12-035c7a98b6d6/scratchpad/audit.YceMXp (deleting only the copy's hgb_delta_test.json to re-run the final test), with the pinned package versions; I edited nothing in /Users/yadi/Downloads/teammate-audit, whose git status, including ignored files, was empty afterwards.

## My verdict

The auditor reported no findings, so no numerical changes are necessary. Instead of trusting variable names or docstrings, the agent ran a direct leakage test by perturbing future target values to verify that no features shifted, recomputed lags against the calendar, and reproduced the committed metrics. I expected risk—their Exercise 4 hgb_delta target (predicting cnt minus cnt_lag_1) which is confirmed by this result. Because cnt_lag_1 relies on the previous day, adding it back to the prediction is a valid inversion and introduces no leakage.

The audit had some limits. It evaluated the code against five mechanical checks, not whether the report's conclusions actually follow from the data, and it only inspected src and tests—meaning CLAUDE.md. This means that the written arguments were never assessed. A clean result here confirms there is no detectable leakage or split error, but not that the overall analysis is sound.
