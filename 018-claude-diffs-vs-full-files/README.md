# #018 Diffs vs full files vs JSON edits (Claude Code CLI)

**Question.** For the same small fix, how many output tokens (and errors) do you get if you ask Claude for the whole file, a unified diff, a JSON list of search/replace edits, or let it use its Edit tool?

**Short answer.** 10 edits × 4 formats = 40 runs, **all 40 applied cleanly and passed** (0 parse errors, 0 apply errors; every diff applied with strict `git apply`, no line-count repair needed). On these tiny files (42–444 output tokens for a whole file), the **whole file was the shortest answer** (146 output tokens mean), JSON search/replace about the same (155), the unified diff 45% longer (211). The agentic Edit-tool route used **3.3× the output tokens** (476 mean: a Read call, an Edit call, plus a short summary) and, with its ~35K-token tool/system prefix over 3 calls, **~1.9× the API-equivalent cost** ($0.057 vs $0.030 per edit).

## Setup
- Claude Code 2.1.300, `claude-opus-5-5`, default effort, Pro sign-in; headless `claude -p … --output-format stream-json --verbose --dangerously-skip-permissions --strict-mcp-config --no-session-persistence --disable-slash-commands`, fresh copy of one SUITE14 package per run.
- Prompt for all arms: "`node test.js` fails. Make it pass by fixing broken.js (never edit test.js). Files: <broken.js, test.js, helpers pasted in>" + one arm-specific instruction (`scripts/make_jobs.py`):
  - **tool**: default tools; "Fix the bug by editing broken.js … with your file-editing tools, then stop."
  - **full / udiff / json**: `--tools ""` (no tools); "Reply with the complete corrected broken.js in one ```js block" / "only a unified diff" / "only a JSON array of exact search/replace edits".
- Grading: `scripts/apply.py` applies the answer (write file / `git apply -p0`, then `--recount` fallback / exact-once string replace) and runs `node test.js`. `scripts/regrade.py` re-grades every no-tool answer offline from the raw stream → `results/graded.csv`.
- 10 edits: N01_median, N02_duration, N03_csv, T02_duplicate, T05_stale, T06_neardup, T07_multihunk, T08_insert, T09_delete, T10_replace_all. 1 run per cell, 3 at a time, 2026-10-14 ~19:52 UTC.
- Est. $ = Claude Code's `total_cost_usd` (list API price). **API-equivalent estimate; Pro isn't billed per token.**

## Exact commands
```bash
source /workspace/tools/setup.sh
python3 scripts/make_jobs.py
scripts/harness/driver_cc.sh scripts/jobs.txt 3 results/driver.log
python3 scripts/regrade.py && /workspace/tools/mlenv/bin/python scripts/analyze.py
```

## Results
| Format | Applied & passed | Output tokens mean (total) | Total tokens mean | Model calls | Est. $ / edit | Wall |
|---|---|---|---|---|---|---|
| Edit tool (agentic) | 10/10 | 476 (4,757) | 39,064 | 3 | $0.057 | 8.6 s |
| Whole file | 10/10 | 146 (1,462) | 4,125 | 1 | $0.030 | 4.4 s |
| Unified diff | 10/10 | 211 (2,114) | 4,218 | 1 | $0.031 | 4.7 s |
| JSON search/replace | 10/10 | 155 (1,545) | 4,180 | 1 | $0.030 | 4.1 s |

Per-edit output tokens in `results/graded.csv` and the chart (`results/chart.png`). Diffs were longest on N03_csv (816 tokens: it rewrote most of the parser, so the diff carried both old and new code).

## Caveats
- Files are tiny (≤ 414 bytes of code). A whole-file reply grows with file size; a diff or JSON edit grows with the change. On a 2,000-line file the ranking would flip; this shows the crossover is above "small file".
- The no-tool arms got the file contents in the prompt and their output was applied by my script; the tool arm had to Read the file (Claude Code requires a Read before Edit) and wrote a closing summary. That's how each is used in practice, but it isn't output-format alone.
- Grader bug during the live run: `patch` isn't installed in this sandbox and a mid-run edit to apply.py briefly broke it, so the live `passed` column is wrong for some no-tool rows. `graded.csv` (offline re-grade from the raw answers) is the source of truth. The one tool-arm run caught by that window (N01_median) was discarded (`raw/tool__N01_median__r1.invalid_grader_bug.jsonl`) and rerun.
- 1 run per cell (Claude's run-to-run variance was ~1% in #010b).
