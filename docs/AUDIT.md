# Audit of a teammate's repository (Exercise 3)

**Repository audited:** https://github.com/aceyq/bikeshare-open.git (HEAD 1082e07; starter commit f78104c)

**How it was run:** the leakage-auditor subagent, from my own repo's Claude Code session (Claude
Sonnet), with the teammate's clone added as a read-only working directory. Prompt: review
git -C ~/Downloads/teammate-audit diff f78104c HEAD -- src tests against the five checks, reading
and running their code, editing nothing.

## Auditor output (verbatim)

> All five checks pass for git diff f78104c HEAD -- src tests (HEAD 1082e07): perturbing same-day or later target values changed none of the 15 features, all lag and rolling values matched calendar-day recomputation, the split is by date with the scaler fit on the 348 training rows only, the 14 dropped rows are exactly the warm-up and gap rows within the tested bound, and both baselines are in every metrics JSON the code writes (23 tests passed, and reports/metrics.json and both hgb_delta JSONs reproduced identically).
>
> As required for runs that write files, I ran the tests and pipeline on a copy at /private/tmp/claude-501/-Users-yadi-Downloads-bikeshare-open-starter/f32308e6-e105-450f-8c12-035c7a98b6d6/scratchpad/audit.YceMXp (deleting only the copy's hgb_delta_test.json to re-run the final test), with the pinned package versions; I edited nothing in /Users/yadi/Downloads/teammate-audit, whose git status, including ignored files, was empty afterwards.

## My verdict

The auditor reported no findings, so none changes a number, and I agree with that for the code it
reviewed. Its evidence is the right kind: it perturbed future target values and confirmed no feature
moved (a direct leakage test, not a reading of names or docstrings), recomputed lags against the
calendar, and reproduced the committed metrics. That covers the one place I expected risk, their
Exercise 4 hgb_delta target (predicting cnt minus cnt_lag_1): since cnt_lag_1 uses only the previous
day, adding it back to the prediction is a valid inversion and introduces no leakage. The limits of
this audit: it checked the code against five mechanical checks, not whether their report's
conclusions follow from the numbers, and it reviewed only src and tests, so their CLAUDE.md, skill
and written arguments were not assessed. A clean result here means "no detectable leakage or split
error", not "the analysis is right".
