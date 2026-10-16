# Diff, whole file, or JSON? On small files, just ask for the whole file.

*Draft. Tech in General experiment #018. 40 headless Claude Code runs (Opus 5.5, Pro), 2026-10-15 IST.*

Ten small bug fixes, each asked four ways: let Claude Code use its Edit tool, or (with tools off) reply with the whole fixed file, a unified diff, or a JSON list of search/replace edits.

All 40 answers applied cleanly and passed. Every diff applied with plain `git apply`, and every JSON edit matched exactly once.

| Format | Output tokens per fix | Est. cost per fix |
|---|---|---|
| Edit tool | 476 | 5.7¢ |
| Whole file | **146** | 3.0¢ |
| Unified diff | 211 | 3.1¢ |
| JSON edits | 155 | 3.0¢ |

**Surprise:** the diff was the *longest* text answer. Context lines and hunk headers cost more than retyping a 10-line file.

**The Edit tool cost the most** because it's a 3-call loop (read the file, edit it, say what it did), each call carrying Claude Code's tool definitions. That's the price of letting the agent work on files itself.

**Don't over-read it.** These files are tiny. Output for "whole file" grows with the file; a diff grows with the change. For real files, diffs or search/replace win; the crossover is somewhere above a screenful.

*$ are API-equivalent estimates from Claude Code's `total_cost_usd`; Pro isn't billed per token.*
