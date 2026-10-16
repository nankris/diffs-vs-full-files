# Should your coding agent answer with a diff or the whole file? (Codex)

Same tiny bug, four ways to ask Codex for the fix: give me the whole file, give me a unified diff, give me a JSON list of "replace this with that", or just go edit it yourself.

**All 40 fixes worked.** Ten bugs, four formats, zero failures. One diff had its line counts wrong and only applied with a forgiving patch mode, so strictly that's 39 clean.

**The shortest answer was the JSON list** (75 output tokens on average). Whole file: 98. Diff: 105. On files this small, a diff is not shorter than the file: it repeats the context lines and both the old and new version of each line it changes.

**Letting Codex edit the file itself cost about 1.7× more**, and it isn't because of the edit. The agent needs two model calls (make the edit, then report), and every call re-sends Codex's ~15K-token instructions and tool definitions. The patch itself is only a few dozen tokens more.

Compared with Claude Opus on the same prompts, Codex was terser in every format (JSON 75 vs 155 tokens; agentic 164 vs 476) and its agentic route was cheaper, because it applied the edit in one shot without a separate "read the file" step.

**Takeaway:** for small, well-specified edits where you already have the file, ask for JSON search/replace edits in a single call. Save the agent loop for when it needs to look around. And if you take diffs from a model, apply them with a fallback that fixes hunk counts.

$ figures are API-equivalent estimates ($0.0075–0.0131 per edit); Plus is a flat subscription.
