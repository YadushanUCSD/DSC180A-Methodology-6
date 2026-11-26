---
name: seed-fault
description: Seed one named fault into src/, record the red test output and the hook's stderr in docs/SEEDED_FAULTS.md, and commit the broken state. Use when asked to seed a fault, break the pipeline on purpose, or test the verification suite.
allowed-tools: Read, Edit, Bash(python -m pytest*), Bash(git diff*), Bash(git status*), Bash(git add*), Bash(git commit*)
---

# Current state

!`git status --short; python -m pytest -q 2>&1 | tail -1`

# Seeding a fault: $ARGUMENTS

1. **Precondition.** The working tree must be clean and the suite green (see
   above). If not, say so and stop.
2. **Seed it.** Make the smallest edit under `src/` that introduces exactly
   the fault described, using the Edit tool so the PostToolUse hook fires.
   Never touch `tests/`, `data/raw/`, or anything outside `src/`.
3. **Record it.** Append a section to `docs/SEEDED_FAULTS.md` titled with the
   fault, containing, pasted verbatim in code blocks:
   - the output of `git diff src/`
   - the hook's stderr (if the hook was silent, write "hook silent" -- that is
     a finding, not a failure of this skill)
   - the output of `python -m pytest -q --tb=short`
4. **If no test went red, say so plainly:** the suite has a gap. Do not add a
   test and do not fix anything here.
5. **Commit the broken state** with message `Seed fault: <description>`, then
   stop. Fixing is a separate task, done in a fresh session so the turns it
   takes can be counted.
