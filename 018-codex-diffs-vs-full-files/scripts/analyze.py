"""#018 Codex arm: tables + chart from results/graded.csv (and the Claude arm's graded.csv for comparison, read-only)."""
import csv, os, statistics as st
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
E = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); R = f"{E}/results"
G = list(csv.DictReader(open(f"{R}/graded.csv")))
FM = ["tool", "full", "udiff", "json"]; TK = sorted({g["task"] for g in G})
summ = []
for fm in FM:
    v = [g for g in G if g["fmt"] == fm]; m = lambda c: st.mean(float(x[c]) for x in v)
    summ.append(dict(fmt=fm, runs=len(v), passed=sum(int(x["passed"]) for x in v),
                     parse_errors=sum(x["status"] == "parse_error" for x in v), apply_errors=sum(x["status"] == "apply_error" for x in v),
                     needed_recount=sum(x["status"] == "ok_recount" for x in v), out_mean=round(m("output_tokens")),
                     out_sum=int(sum(float(x["output_tokens"]) for x in v)), total_mean=round(m("total_tokens")),
                     calls_mean=round(m("model_calls"), 2), tool_calls_mean=round(m("tool_calls"), 2),
                     est_cost_mean=round(m("est_cost_usd"), 4), wall_mean=round(m("wall_s"), 1)))
with open(f"{R}/summary.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(summ[0])); w.writeheader(); w.writerows(summ)
with open(f"{R}/per_task_output_tokens.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["task"] + FM)
    for t in TK: w.writerow([t] + [next(g["output_tokens"] for g in G if g["task"] == t and g["fmt"] == fm) for fm in FM])
for s in summ: print(s)
cl = {}
cp = "/workspace/work/tig/018-claude-diffs-vs-full-files/results/graded.csv"
if os.path.exists(cp):
    C = list(csv.DictReader(open(cp)))
    fk = "fmt" if "fmt" in C[0] else ("mode" if "mode" in C[0] else "cond")
    for fm in FM:
        v = [float(c["output_tokens"]) for c in C if c[fk] == fm]
        if v: cl[fm] = st.mean(v)
    print("claude", cl)
fig, ax = plt.subplots(1, 2, figsize=(14, 4.8), gridspec_kw={"width_ratios": [2.2, 1]})
x = np.arange(len(TK)); bw = .2; col = dict(tool="tab:gray", full="tab:blue", udiff="tab:orange", json="tab:green")
for i, fm in enumerate(FM):
    y = [float(next(g["output_tokens"] for g in G if g["task"] == t and g["fmt"] == fm)) for t in TK]
    ax[0].bar(x + (i - 1.5) * bw, y, bw, label=fm, color=col[fm])
ax[0].set_xticks(x); ax[0].set_xticklabels([t.split("_", 1)[0] + "\n" + t.split("_", 1)[1] for t in TK], fontsize=8)
ax[0].set_ylabel("output tokens"); ax[0].set_title("Codex output tokens per edit, by answer format (all 40 applied & passed)"); ax[0].legend()
m = [s["out_mean"] for s in summ]
ax[1].bar(np.arange(4) - .2, m, .4, color=[col[f] for f in FM], label="Codex gpt-6.1-sol")
if cl: ax[1].bar(np.arange(4) + .2, [cl.get(f, 0) for f in FM], .4, color=[col[f] for f in FM], alpha=.4, hatch="//", label="Claude Opus 5.5 (018-claude)")
for i, s in enumerate(summ): ax[1].text(i - .2, s["out_mean"] + 5, f"{s['out_mean']}\n${s['est_cost_mean']:.4f}", ha="center", fontsize=8)
ax[1].set_xticks(range(4)); ax[1].set_xticklabels(FM); ax[1].set_ylabel("mean output tokens"); ax[1].legend(fontsize=8)
ax[1].set_title("Mean output tokens (label: Codex est. $/edit)"); ax[1].set_ylim(0, max(m + list(cl.values())) * 1.25)
fig.tight_layout(); fig.savefig(f"{R}/chart.png", dpi=110)
