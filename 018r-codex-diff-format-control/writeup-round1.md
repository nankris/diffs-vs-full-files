# 018r results — round 1

**Verdict: STILL INCONCLUSIVE.** This verdict concerns H1: JSON edits reduce output versus whole files on the large fixtures in both workflows. It does not prove a universal best format or a reliability advantage.

156 calls, 152 applied and passed (including recount fallback), 156 workflow compliant. GPU: none. Experiment CU: **0**.

|Size|Workflow|Format|Pass / n|Strict pass|Protocol valid|Mean output tokens|Mean total tokens|Tool calls mean|
|---|---|---|---:|---:|---:|---:|---:|---:|
|small|off|full|20/20|20|20|93.9|14064.7|0.0|
|small|off|udiff|19/20|18|20|118.8|14107.6|0.0|
|small|off|json|20/20|20|20|84.5|14080.2|0.0|
|small|on|full|20/20|20|20|183.8|29648.0|1.0|
|small|on|udiff|19/20|19|20|211.1|31485.8|1.1|
|small|on|json|20/20|20|20|153.3|29637.2|1.0|
|large|off|full|6/6|6|6|1836.0|19014.7|0.0|
|large|off|udiff|4/6|3|6|248.8|17445.5|0.0|
|large|off|json|6/6|6|6|129.7|17333.3|0.0|
|large|on|full|6/6|6|6|257.2|39832.2|1.2|
|large|on|udiff|6/6|6|6|360.7|49233.0|1.7|
|large|on|json|6/6|6|6|245.3|43518.0|1.3|

Paired task-cluster bootstrap (20,000 resamples; geometric mean ratios; 95% percentile CI). Ratios above 1 favor the sparse format (JSON or diff) for format comparisons and indicate overhead for workflow comparisons. Repetitions are averaged within each task before computing ratios.

|Comparison|Ratio|95% CI|
|---|---:|---|
|large_full_over_json_off|16.194|[9.057, 31.246]|
|small_full_over_json_off|1.121|[0.815, 1.475]|
|large_full_over_json_on|1.075|[0.991, 1.221]|
|small_full_over_json_on|1.192|[1.048, 1.353]|
|large_full_over_udiff_off|7.786|[5.316, 11.028]|
|small_full_over_udiff_off|0.752|[0.591, 0.973]|
|large_full_over_udiff_on|0.726|[0.463, 0.924]|
|small_full_over_udiff_on|0.882|[0.781, 1.000]|
|total_on_over_off_full|2.095|[2.037, 2.157]|
|total_on_over_off_udiff|2.318|[2.146, 2.537]|
|total_on_over_off_json|2.169|[2.101, 2.307]|

## Interpretation and limits

The fully crossed design estimates format differences within a fixed workflow and workflow differences within a fixed format. The on arm requires writing an answer artifact, while off returns text. This is the intended workflow treatment, not a literal removal of every tool definition. Audit compliance and tool types in runs CSV/raw streams; cached-input variation means token totals are not dollar costs.

Tools-on whole-file artifacts can be synthesized by a short script reading broken.js, so artifact length is not model output length. This allowed behavior is part of the workflow treatment and prevents attributing all savings to representation syntax. The initial three large fixtures are the original median, duration and CSV modules prefixed with 330 unchanged helper lines. They isolate whole-file scaling with unchanged context. They are not three real production files, nor evidence about complex maintenance. Bootstrap intervals describe this synthetic suite; only three large task clusters give limited external validity. Grading always starts from a pristine fixture and preserves tests; unified diffs use strict git apply first, then recount, reported separately. Failures and protocol violations remain in all descriptive and secondary cost comparisons (intention-to-treat); only the primary hypothesis has the prespecified all-valid gate. Secondary diff comparisons therefore characterize assigned workflows including errors, not valid-only patch performance.

Original: ../018-codex-diffs-vs-full-files (untouched). Commands: source /workspace/tools/setup.sh; python3 run.py 1; /workspace/tools/mlenv/bin/python analyze.py 1. CLI 0.162.1, gpt-6.1-sol, low reasoning. Exact prompts and commands are recorded per call. Hypothesis and stopping rule were written in README before execution.
