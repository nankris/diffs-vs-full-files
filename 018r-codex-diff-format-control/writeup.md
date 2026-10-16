# 018r results — round 2

**Verdict: PROVEN.** This verdict concerns H1: JSON edits reduce output versus whole files on the large fixtures in both workflows. It does not prove a universal best format or a reliability advantage.

192 calls, 185 applied and passed (including recount fallback), 191 workflow compliant. GPU: none. Experiment CU: **0**.

|Size|Workflow|Format|Pass / n|Strict pass|Protocol valid|Mean output tokens|Mean total tokens|Tool calls mean|
|---|---|---|---:|---:|---:|---:|---:|---:|
|small|off|full|20/20|20|20|93.9|14064.7|0.0|
|small|off|udiff|18/20|18|20|134.1|14122.9|0.0|
|small|off|json|20/20|20|20|85.5|14081.3|0.0|
|small|on|full|20/20|20|20|179.2|29823.8|1.0|
|small|on|udiff|18/20|18|19|213.8|30953.2|1.1|
|small|on|json|20/20|20|20|149.9|29817.2|1.0|
|large|off|full|12/12|12|12|1892.8|18089.0|0.0|
|large|off|udiff|10/12|10|12|157.3|16371.5|0.0|
|large|off|json|12/12|12|12|110.0|16331.2|0.0|
|large|on|full|12/12|12|12|2336.2|38595.4|1.0|
|large|on|udiff|11/12|7|12|244.3|34418.8|1.0|
|large|on|json|12/12|12|12|186.0|34342.1|1.0|

Paired task-cluster bootstrap (20,000 resamples; geometric mean ratios; 95% percentile CI). Ratios above 1 favor the sparse format (JSON or diff) for format comparisons and indicate overhead for workflow comparisons. Repetitions are averaged within each task before computing ratios.

|Comparison|Ratio|95% CI|
|---|---:|---|
|large_full_over_json_off|19.272|[13.031, 27.327]|
|small_full_over_json_off|1.122|[0.796, 1.519]|
|large_full_over_json_on|13.215|[10.122, 16.658]|
|small_full_over_json_on|1.175|[1.014, 1.365]|
|large_full_over_udiff_off|13.071|[9.450, 18.706]|
|small_full_over_udiff_off|0.697|[0.570, 0.862]|
|large_full_over_udiff_on|10.471|[7.271, 14.063]|
|small_full_over_udiff_on|0.853|[0.748, 0.978]|
|total_on_over_off_full|2.127|[2.120, 2.132]|
|total_on_over_off_udiff|2.144|[2.111, 2.204]|
|total_on_over_off_json|2.113|[2.107, 2.119]|

## Interpretation and limits

The fully crossed design estimates format differences within a fixed workflow and workflow differences within a fixed format. The on arm requires writing an answer artifact, while off returns text. This is the intended workflow treatment, not a literal removal of every tool definition. Audit compliance and tool types in runs CSV/raw streams; cached-input variation means token totals are not dollar costs.

In round 1, tools-on whole-file artifacts could be synthesized by a short script. Round 2 forbids that shortcut and audits literal payload emission. The initial three large fixtures are the original median, duration and CSV modules prefixed with 330 unchanged helper lines. They isolate whole-file scaling with unchanged context. They are not three real production files, nor evidence about complex maintenance. Bootstrap intervals describe this synthetic suite; six large task clusters give limited external validity. Small and large variants share base bugs, so secondary workflow CIs should not be treated as independent production-task evidence. Grading always starts from a pristine fixture and preserves tests; unified diffs use strict git apply first, then recount, reported separately. Failures and protocol violations remain in all descriptive and secondary cost comparisons (intention-to-treat); only the primary hypothesis has the prespecified all-valid gate. Secondary diff comparisons therefore characterize assigned workflows including errors, not valid-only patch performance.

Original: ../018-codex-diffs-vs-full-files (untouched). Commands: source /workspace/tools/setup.sh; python3 run.py 1; /workspace/tools/mlenv/bin/python analyze.py 1. CLI 0.162.1, gpt-6.1-sol, low reasoning. Exact prompts and commands are recorded per call. Hypothesis and stopping rule were written in README before execution.

H2 is supported within every format: the 95% CIs for tools-on/off total-token ratios all exceed 1 (about 2.11–2.14×). These are total-token ratios, not dollar ratios. The diff crossover appears in both workflows: whole-file/diff output ratios are below 1 on small tasks and above 1 on large tasks, with all four CIs excluding 1. Diffs have 7 application failures and 4 recount-only successes; one small diff run violates the single-command rule. Whole-file and JSON each pass 64/64 with full protocol compliance.

## Final round and comparison with round 1

Round 1 was STILL INCONCLUSIVE: large full/JSON ratio off 16.194 [9.057,31.246], on 1.075 [0.991,1.221]. Tools-on could regenerate full artifacts from the source. See writeup-round1.md and chart-round1.png. Round 2 removes that shortcut: all tools-on artifacts must be literal cat heredocs, verified against the saved bytes. It adds three large variants (multihunk, duplicate and replace-all), giving six large task clusters. The final verdict applies to this literal serialization control. Round 1 remains the unconstrained workflow result. There will be no third round. No pooling across protocols.

Round-2 commands: python3 run.py 2; /workspace/tools/mlenv/bin/python analyze.py 2. All 16 tasks × 3 formats × 2 workflows × 2 repetitions = 192 calls.
