# #018 Diffs vs full files vs JSON edits (Codex CLI arm)

**Question.** For the same small fix, how many output tokens (and errors) do you get if you ask Codex for the whole file, a unified diff, a JSON list of search/replace edits, or let it edit with its own tools? Codex counterpart of `018-claude-diffs-vs-full-files` (same 10 edits, same prompts).

**Short answer (this build, these tasks).** 10 edits × 4 formats = 40 runs, **all 40 applied and passed**: 0 parse errors, 0 apply errors. One unified diff (N03_csv) had wrong hunk line counts and only applied with `git apply --recount`; strictly, udiff was 9/10 clean.
- **JSON search/replace was the shortest answer**: 75 output tokens mean, vs whole file 98, unified diff 105.
- **Letting Codex edit with its tools** used 164 output tokens (1.7× JSON) and, because it's 2 model calls each re-sending Codex's ~13–15K-token prefix, **~1.7× the API-equivalent cost** ($0.0131 vs $0.0075–0.0084 per edit) and ~1.8× the wall time (12.1 s vs 6.5–7.0 s).
- Codex was terser than Claude Opus in every format (Claude arm: tool 476, full 146, udiff 211, JSON 155 output tokens), and its agentic route was much cheaper than Claude's (2 calls / 30K tokens vs 3 calls / 39K), because Codex made the edit in one shell call with no separate read step.

On files this small (74–429 bytes) the format barely matters; the fixed prompt prefix dominates. The ranking will change with file size: a whole file grows with the file, a diff or JSON edit with the change.

## Setup
- Codex CLI `codex-cli 0.162.1`, model `gpt-6.1-sol`, default reasoning effort, ChatGPT Plus login; headless `codex exec --json --skip-git-repo-check -o .codex_answer.txt …` on a fresh copy of one `SUITE14` package per run (shared harness `scripts/harness/run_one.py`, extended here with `--flag` and `--sandbox` passthrough).
- Prompt for all arms (`scripts/make_jobs.py`, identical text to the Claude arm): "`node test.js` fails. Make it pass by fixing broken.js (never edit test.js). Files: <broken.js, test.js, any data file pasted in>" + one arm instruction:
  - **tool**: "Fix the bug by editing broken.js … with your file-editing tools, then stop. Don't run anything else…" (`--dangerously-bypass-approvals-and-sandbox`; the agent edits the file itself).
  - **full / udiff / json**: "Do not use any tools. Reply with the complete corrected broken.js in one ```js block" / "only a unified diff …" / "only a JSON array of exact search/replace edits …". Codex has no switch to remove its tools, so these ran with `-s read-only` and the instruction; **no run in these arms made a tool call** (`tool_calls` = 0 in all 30).
- Grading: `scripts/apply.py` applies the final message (write file / `git apply -p0`, falling back to `--recount` / exact-once string replace) and runs `node test.js`. `scripts/regrade.py` re-grades every no-tool answer offline from the raw stream in a fresh fixture copy → `results/graded.csv` (matches the live grade).
- 10 edits: N01_median, N02_duration, N03_csv, T02_duplicate, T05_stale, T06_neardup, T07_multihunk, T08_insert, T09_delete, T10_replace_all. 1 run per cell, 3 at a time, 2026-10-14 20:12–20:14 UTC (2026-10-15 01:42–01:44 IST).
- Cost: gpt-6.1-sol API list price $2.00/M uncached input, $0.10/M cached, $10.00/M output (https://developers.openai.com/api/docs/models/gpt-6.1-sol, checked 2026-10-14). **API-equivalent estimates only; Plus is a flat subscription.**

## Exact commands
```bash
source /workspace/tools/setup.sh
python3 scripts/make_jobs.py
scripts/driver.sh scripts/jobs.txt 3 results/driver.log
python3 scripts/regrade.py && /workspace/tools/mlenv/bin/python scripts/analyze.py
```

## Results
| Format | Applied & passed | Parse / apply errors | Output tokens mean (total) | Total tokens mean | Model calls | Est. $ / edit | Wall |
|---|---|---|---|---|---|---|---|
| Edit with tools (agentic) | 10/10 | 0 / 0 | 164 (1,637) | 30,352 | 2 | $0.0131 | 12.1 s |
| Whole file | 10/10 | 0 / 0 | 98 (985) | 15,121 | 1 | $0.0077 | 6.8 s |
| Unified diff | 10/10 (9 strict, 1 needed `--recount`) | 0 / 0 | 105 (1,051) | 15,462 | 1 | $0.0084 | 7.0 s |
| JSON search/replace | 10/10 | 0 / 0 | 75 (752) | 15,128 | 1 | $0.0075 | 6.5 s |

Output tokens per edit (`results/per_task_output_tokens.csv`):

| Task | tool | full | udiff | json |
|---|---|---|---|---|
| N01_median | 146 | 132 | 99 | 49 |
| N02_duration | 173 | 167 | 196 | 118 |
| N03_csv | 309 | 298 | 204 | 211 |
| T02_duplicate | 142 | 80 | 62 | 53 |
| T05_stale | 124 | 57 | 71 | 36 |
| T06_neardup | 137 | 75 | 69 | 38 |
| T07_multihunk | 174 | 58 | 114 | 71 |
| T08_insert | 133 | 37 | 65 | 36 |
| T09_delete | 116 | 30 | 60 | 32 |
| T10_replace_all | 183 | 51 | 111 | 108 |

Chart: `results/chart.png` (per-edit output tokens by format; mean per format, Codex vs the Claude arm).

### What the numbers say
1. **No reliability gap at this size.** Every format worked; the only blemish was one diff with bad hunk counts, which strict `git apply` rejects. In a pipeline without a `--recount` fallback that's a 10% failure rate for diffs.
2. **Diffs weren't shorter than the whole file** on these files: the diff carries context lines and old + new versions of each changed line. They only won where the file was largest (N03_csv: 204 vs 298).
3. **JSON edits were the cheapest on output** in 9/10 tasks (ties or near-ties on T08/T09, where the whole file is ~100 bytes).
4. **The agentic edit's cost is the second call, not the patch.** Output was only ~60–90 tokens above the text formats, but the second model call re-sent the ~15K prefix.

## Caveats
- Tiny files; the crossover where diffs/JSON beat whole files on output is above "small file" (see N03_csv).
- The no-tool arms rely on an instruction plus a read-only sandbox, not a removed toolset; Codex obeyed in all 30 runs.
- The no-tool arms got the files pasted in; the tool arm also had them pasted, so it didn't need to read (that's why Codex's tool route was 2 calls, while Claude's needed a Read first).
- 1 run per cell. The same account ran #020's Codex arm in the same minutes.

## Files
- `scripts/make_jobs.py`, `scripts/prompts/` (exact prompt per run), `scripts/jobs.txt`, `scripts/driver.sh`, `scripts/apply.py`, `scripts/regrade.py`, `scripts/analyze.py`, `scripts/harness/` (harness copy with `--flag`/`--sandbox`, fixtures)
- `results/runs.csv`, `results/graded.csv`, `results/summary.csv`, `results/per_task_output_tokens.csv`, `results/apply_log.csv`, `results/chart.png`, `results/driver.log`, `results/raw/*.jsonl`, `results/probe/` (one pre-run probe, excluded)
