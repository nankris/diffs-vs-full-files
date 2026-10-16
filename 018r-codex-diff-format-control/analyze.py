import csv,json,pathlib,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
E=pathlib.Path(__file__).resolve().parent
rnd=int(sys.argv[1]); rows=json.loads((E/f'round{rnd}.json').read_text())
rng=np.random.default_rng(1801)
def boot(v):
    v=np.array(v); draws=rng.choice(v,(20000,len(v)),replace=True).mean(axis=1)
    return [float(np.exp(v.mean())),*map(float,np.exp(np.percentile(draws,[2.5,97.5])))]
def avg(task,fmt,w,metric):
    rs=[r for r in rows if r['task']==task and r['format']==fmt and r['workflow']==w]
    return np.mean([r[metric] for r in rs])
tasks=sorted({r['task'] for r in rows}); large=[t for t in tasks if t.startswith('L')]
comparisons={}
valid=all(r['passed'] and r['compliant'] and r['rc']==0 and r['output'] is not None for r in rows if r['size']=='large' and r['format'] in ['full','json'])
for w in ['off','on']:
    comparisons['large_full_over_json_'+w]=boot([np.log(avg(t,'full',w,'output')/avg(t,'json',w,'output')) for t in large])
    comparisons['small_full_over_json_'+w]=boot([np.log(avg(t,'full',w,'output')/avg(t,'json',w,'output')) for t in tasks if not t.startswith('L')])
for w in ['off','on']:
 for size,ts in [('large',large),('small',[t for t in tasks if not t.startswith('L')])]:
    comparisons[size+'_full_over_udiff_'+w]=boot([np.log(avg(t,'full',w,'output')/avg(t,'udiff',w,'output')) for t in ts])
for f in ['full','udiff','json']:
    comparisons['total_on_over_off_'+f]=boot([np.log(avg(t,f,'on','total')/avg(t,f,'off','total')) for t in tasks])
primary=[comparisons['large_full_over_json_'+w] for w in ['off','on']]
verdict='PROVEN' if valid and all(c[1]>1 for c in primary) else 'DISPROVEN' if valid and any(c[2]<1 for c in primary) else 'STILL INCONCLUSIVE'
out=dict(round=rnd,verdict=verdict,primary_cells_valid=valid,comparisons=comparisons,runs=len(rows),passes=sum(r['passed'] for r in rows),compliant=sum(r['compliant'] for r in rows))
(E/f'analysis{rnd}.json').write_text(json.dumps(out,indent=2))
with (E/f'runs{rnd}.csv').open('w') as fp:
    wr=csv.DictWriter(fp,fieldnames=rows[0].keys());wr.writeheader();wr.writerows(rows)
lines=[f'# 018r results — round {rnd}',f'\n**Verdict: {verdict}.** This verdict concerns H1: JSON edits reduce output versus whole files on the large fixtures in both workflows. It does not prove a universal best format or a reliability advantage.',f'\n{len(rows)} calls, {out["passes"]} applied and passed (including recount fallback), {out["compliant"]} workflow compliant. GPU: none. Experiment CU: **0**.', '\n|Size|Workflow|Format|Pass / n|Strict pass|Protocol valid|Mean output tokens|Mean total tokens|Tool calls mean|','|---|---|---|---:|---:|---:|---:|---:|---:|']
summary=[]
for size in ['small','large']:
 for w in ['off','on']:
  for f in ['full','udiff','json']:
   rs=[r for r in rows if r['size']==size and r['workflow']==w and r['format']==f]
   a=dict(size=size,workflow=w,format=f,n=len(rs),passed=sum(r['passed'] for r in rs),strict=sum(r['status']=='ok' for r in rs),compliant=sum(r['compliant'] for r in rs),output=float(np.mean([r['output'] for r in rs])),total=float(np.mean([r['total'] for r in rs])),tools=float(np.mean([r['tool_calls'] for r in rs])))
   summary.append(a); lines.append(f'|{size}|{w}|{f}|{a["passed"]}/{a["n"]}|{a["strict"]}|{a["compliant"]}|{a["output"]:.1f}|{a["total"]:.1f}|{a["tools"]:.1f}|')
lines+=['\nPaired task-cluster bootstrap (20,000 resamples; geometric mean ratios; 95% percentile CI). Ratios above 1 favor the sparse format (JSON or diff) for format comparisons and indicate overhead for workflow comparisons. Repetitions are averaged within each task before computing ratios.','\n|Comparison|Ratio|95% CI|','|---|---:|---|']
for k,(m,lo,hi) in comparisons.items():lines.append(f'|{k}|{m:.3f}|[{lo:.3f}, {hi:.3f}]|')
lines+=['\n## Interpretation and limits','\nThe fully crossed design estimates format differences within a fixed workflow and workflow differences within a fixed format. The on arm requires writing an answer artifact, while off returns text. This is the intended workflow treatment, not a literal removal of every tool definition. Audit compliance and tool types in runs CSV/raw streams; cached-input variation means token totals are not dollar costs.','\nTools-on whole-file artifacts can be synthesized by a short script reading broken.js, so artifact length is not model output length. This allowed behavior is part of the workflow treatment and prevents attributing all savings to representation syntax. The initial three large fixtures are the original median, duration and CSV modules prefixed with 330 unchanged helper lines. They isolate whole-file scaling with unchanged context. They are not three real production files, nor evidence about complex maintenance. Bootstrap intervals describe this synthetic suite; only three large task clusters give limited external validity. Grading always starts from a pristine fixture and preserves tests; unified diffs use strict git apply first, then recount, reported separately. Failures and protocol violations remain in all descriptive and secondary cost comparisons (intention-to-treat); only the primary hypothesis has the prespecified all-valid gate. Secondary diff comparisons therefore characterize assigned workflows including errors, not valid-only patch performance.','\nOriginal: ../018-codex-diffs-vs-full-files (untouched). Commands: source /workspace/tools/setup.sh; python3 run.py 1; /workspace/tools/mlenv/bin/python analyze.py 1. CLI 0.162.1, gpt-6.1-sol, low reasoning. Exact prompts and commands are recorded per call. Hypothesis and stopping rule were written in README before execution.']
if rnd==2:
 lines=[line.replace('Tools-on whole-file artifacts can be synthesized by a short script reading broken.js, so artifact length is not model output length. This allowed behavior is part of the workflow treatment and prevents attributing all savings to representation syntax.', 'In round 1, tools-on whole-file artifacts could be synthesized by a short script. Round 2 forbids that shortcut and audits literal payload emission.').replace('only three large task clusters give limited external validity.', 'six large task clusters give limited external validity. Small and large variants share base bugs, so secondary workflow CIs should not be treated as independent production-task evidence.') for line in lines]
 lines+=['\nH2 is supported within every format: the 95% CIs for tools-on/off total-token ratios all exceed 1 (about 2.11–2.14×). These are total-token ratios, not dollar ratios. The diff crossover appears in both workflows: whole-file/diff output ratios are below 1 on small tasks and above 1 on large tasks, with all four CIs excluding 1. Diffs have 7 application failures and 4 recount-only successes; one small diff run violates the single-command rule. Whole-file and JSON each pass 64/64 with full protocol compliance.']
 lines+=['\n## Final round and comparison with round 1', '\nRound 1 was STILL INCONCLUSIVE: large full/JSON ratio off 16.194 [9.057,31.246], on 1.075 [0.991,1.221]. Tools-on could regenerate full artifacts from the source. See writeup-round1.md and chart-round1.png. Round 2 removes that shortcut: all tools-on artifacts must be literal cat heredocs, verified against the saved bytes. It adds three large variants (multihunk, duplicate and replace-all), giving six large task clusters. The final verdict applies to this literal serialization control. Round 1 remains the unconstrained workflow result. There will be no third round. No pooling across protocols.', '\nRound-2 commands: python3 run.py 2; /workspace/tools/mlenv/bin/python analyze.py 2. All 16 tasks × 3 formats × 2 workflows × 2 repetitions = 192 calls.']
(E/'writeup.md').write_text('\n'.join(lines)+'\n')
(E/f'summary{rnd}.json').write_text(json.dumps(summary,indent=2))
fig,axes=plt.subplots(1,2,figsize=(11,4))
colors=['#4477aa','#ee6677','#228833']
for ax,size in zip(axes,['small','large']):
 for i,f in enumerate(['full','udiff','json']):
  vals=[next(a['output'] for a in summary if a['size']==size and a['workflow']==w and a['format']==f) for w in ['off','on']]
  ax.bar(np.arange(2)+(i-1)*.24,vals,width=.23,label=f,color=colors[i])
 ax.set_xticks([0,1],['Tools off','Tools on']);ax.set_title(size.capitalize()+' fixtures');ax.set_ylabel('Mean output tokens');ax.legend()
fig.suptitle(f'018r round {rnd}: format × workflow ({verdict})');fig.tight_layout();fig.savefig(E/'chart.png',dpi=180)
print(json.dumps(out,indent=2))
