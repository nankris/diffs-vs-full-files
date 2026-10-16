import csv, statistics as S, os
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = list(csv.DictReader(open(f"{D}/results/graded.csv")))
arms = ["tool","full","udiff","json"]; lab={"tool":"Edit tool (agentic)","full":"whole file in reply","udiff":"unified diff in reply","json":"JSON search/replace"}
out=[]
for a in arms:
    rs=[r for r in rows if r["cond"]==a]
    out.append(dict(arm=a, n=len(rs), ok=sum(r["status"]=="ok" for r in rs),
        errors=";".join(f"{r['task']}:{r['status']}" for r in rs if r["status"]!="ok") or "none",
        output_tokens_mean=round(S.mean(int(r["output_tokens"]) for r in rs),1),
        output_tokens_total=sum(int(r["output_tokens"]) for r in rs),
        total_tokens_mean=round(S.mean(int(r["total_tokens"]) for r in rs)),
        est_cost_mean=round(S.mean(float(r["est_cost_usd"]) for r in rs),4),
        turns_mean=round(S.mean(int(r["num_turns"]) for r in rs),2), wall_mean=round(S.mean(float(r["wall_s"]) for r in rs),1)))
per={}
for r in rows: per.setdefault(r["task"],{})[r["cond"]]=int(r["output_tokens"])
w=csv.DictWriter(open(f"{D}/results/summary.csv","w"),fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
for o in out: print(o)
tasks=sorted(per); x=np.arange(len(tasks))
fig,ax=plt.subplots(1,2,figsize=(14,4.8),gridspec_kw={"width_ratios":[2.2,1]})
cols={"tool":"#999","full":"#d17b4a","udiff":"#4a7bd1","json":"#5aa36b"}
for i,a in enumerate(arms):
    ax[0].bar(x+(i-1.5)*0.2,[per[t][a] for t in tasks],0.2,label=lab[a],color=cols[a])
ax[0].set_xticks(x); ax[0].set_xticklabels(tasks,rotation=30,fontsize=8); ax[0].set_ylabel("output tokens"); ax[0].legend(fontsize=8); ax[0].set_title("Output tokens per edit (10 edits, all 40 applied & passed)")
ax[1].bar([lab[a].replace(" ","\n",1) for a in arms],[o["est_cost_mean"] for o in out],color=[cols[a] for a in arms])
for i,o in enumerate(out): ax[1].text(i,o["est_cost_mean"],f"${o['est_cost_mean']:.3f}",ha="center",va="bottom",fontsize=9)
ax[1].set_title("API-equivalent est. $ per edit (mean)"); ax[1].tick_params(axis="x",labelsize=8)
plt.tight_layout(); plt.savefig(f"{D}/results/chart.png",dpi=110)
