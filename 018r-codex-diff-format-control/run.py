import concurrent.futures as cf, hashlib, json, os, pathlib, random, shutil, subprocess, sys, time
E=pathlib.Path(__file__).resolve().parent
PK=['N01_median','N02_duration','N03_csv','T02_duplicate','T05_stale','T06_neardup','T07_multihunk','T08_insert','T09_delete','T10_replace_all']
FMT={'full':'The complete corrected broken.js in one ```js block.', 'udiff':'Only a unified diff with --- broken.js and +++ broken.js headers and valid @@ hunk counts, in one ```diff block.', 'json':'Only a JSON array of exact search/replace edits [{"old":"exact existing text","new":"replacement"}] in one ```json block. Each old string must occur exactly once.'}
def fixtures(round):
    tasks=PK[:]
    for i,base in enumerate(['N01_median','N02_duration','N03_csv']):
        name=f'L{i+1:02d}_{base}'; dst=E/'fixtures'/name
        if not dst.exists():
            shutil.copytree(E/'fixtures'/base,dst)
            src=(dst/'broken.js').read_text()
            # Independent inert helper functions, preserving exports and tests.
            pad=''.join(f'function referenceHelper{j:03d}(x) {{\n  return x + {j};\n}}\n' for j in range(110))
            (dst/'broken.js').write_text(pad+src)
        tasks.append(name)
    if round==2:
        for i,base in enumerate(['T07_multihunk','T02_duplicate','T10_replace_all']):
            name=f'L{i+4:02d}_{base}'; dst=E/'fixtures'/name
            if not dst.exists():
                shutil.copytree(E/'fixtures'/base,dst)
                src=(dst/'broken.js').read_text().splitlines(True)
                # Spread unchanged helpers before and after the edited module.
                def pad(start): return ''.join(f'function extraHelper{j:03d}(v) {{\n  const offset = {j};\n  return v - offset;\n}}\n' for j in range(start,start+45))
                (dst/'broken.js').write_text(pad(0)+''.join(src)+pad(45))
            tasks.append(name)
    return tasks

def run(job):
    rnd,task,fmt,workflow,rep=job; ident=f'r{rnd}_{task}_{fmt}_{workflow}_{rep}'
    dest=E/'results'/ident; dest.mkdir(parents=True,exist_ok=True)
    if (dest/'result.json').exists(): return json.loads((dest/'result.json').read_text())
    work=E/'work'/ident
    if work.exists(): shutil.rmtree(work)
    shutil.copytree(E/'fixtures'/task,work)
    files=''.join(f'\n{p.name}:\n```\n{p.read_text()}\n```\n' for p in sorted(work.iterdir()) if p.is_file())
    prompt='Fix broken.js so node test.js passes. Never alter test.js or other fixture files. All relevant files are provided below.\n'+files+'\nRequested representation: '+FMT[fmt]
    if workflow=='on': prompt+='\nUse your shell tool to write exactly this representation to answer.txt in the current directory. Do not apply the edits or run tests. Then reply Done. Do not delegate.'
    else: prompt+='\nDo not use any tools. Return exactly the requested representation as your final answer. Do not delegate.'
    if rnd==2 and workflow=='on':
        prompt+='\nROUND 2 SERIALIZATION CONTROL: Use exactly ONE shell command: cat > answer.txt <<\'ANSWER_EOF\' followed by the complete literal requested representation and the closing ANSWER_EOF line. You must emit every byte of the artifact literally in the command. Do not read any files, use Python/JavaScript/sed, perform replacements, copy files, or synthesize contents programmatically. Use only cat and the quoted heredoc. All source content is already pasted above.'
    (dest/'prompt.txt').write_text(prompt)
    cmd=['codex','exec','--json','--ephemeral','--ignore-user-config','--skip-git-repo-check','-m','gpt-6.1-sol','-c','model_reasoning_effort="low"','--disable','multi_agent','--disable','apps','--disable','plugins','--disable','skill_search','-C',str(work),'-o',str(dest/'final.txt')]
    if workflow=='on': cmd+=['--dangerously-bypass-approvals-and-sandbox']
    else: cmd+=['-s','read-only','--disable','shell_tool']
    (dest/'command.json').write_text(json.dumps(cmd))
    t=time.monotonic(); timeout=False
    with (dest/'events.jsonl').open('w') as out,(dest/'stderr.txt').open('w') as err:
        try: proc=subprocess.run(cmd+['-'],input=prompt,text=True,stdout=out,stderr=err,timeout=240); rc=proc.returncode
        except subprocess.TimeoutExpired: timeout=True; rc=124
    events=[]
    for line in (dest/'events.jsonl').read_text().splitlines():
        try: events.append(json.loads(line))
        except ValueError: pass
    turns=[e for e in events if e.get('type')=='turn.completed']; usage={}
    for e in turns:
        for k,v in e.get('usage',{}).items():
            if isinstance(v,(int,float)): usage[k]=usage.get(k,0)+v
    items=[e.get('item',{}) for e in events if e.get('type')=='item.completed']
    toolitems=[i for i in items if i.get('type') not in ['agent_message','reasoning']]
    calls=len(toolitems)
    literal_valid=True
    if rnd==2 and workflow=='on':
        commands=[i.get('command','') for i in toolitems if i.get('type')=='command_execution']
        # Compare the literal heredoc payload with the actual artifact after execution.
        import re
        if len(commands)!=1: literal_valid=False
        else:
            cmdtext=commands[0]
            # CLI wraps command text with shell quoting; shlex recovers -c argument.
            import shlex
            try:
                parts=shlex.split(cmdtext); script=parts[-1] if '-lc' in parts or '-c' in parts else cmdtext
                match=re.fullmatch(r"\s*cat\s*>\s*answer\.txt\s*<<'ANSWER_EOF'\n(.*)\nANSWER_EOF\s*",script,re.S)
                literal_valid=bool(match)
                if match and (work/'answer.txt').exists(): literal_valid=(work/'answer.txt').read_text()==match.group(1)+'\n'
            except Exception: literal_valid=False
    artifact=work/'answer.txt' if workflow=='on' else dest/'final.txt'
    answer=artifact.read_text() if artifact.exists() else ''
    (dest/'answer.txt').write_text(answer)
    compliant=(calls>0 if workflow=='on' else calls==0)
    # Grading in a fresh copy prevents tool-side mutations from affecting results.
    grade=work/'grade'; shutil.copytree(E/'fixtures'/task,grade)
    (grade/'.codex_answer.txt').write_text(answer)
    env=dict(os.environ,APPLY_LOG=str(dest/'apply_log.csv'))
    g=subprocess.run([sys.executable,str(E/'apply.py'),fmt],cwd=grade,env=env,text=True,capture_output=True,timeout=70)
    (dest/'grade.log').write_text(g.stdout+g.stderr)
    status=(grade/'.apply_status').read_text() if (grade/'.apply_status').exists() else 'grader_error'
    mutated=any((work/p.name).read_bytes()!=p.read_bytes() for p in (E/'fixtures'/task).iterdir() if p.is_file())
    row=dict(id=ident,round=rnd,task=task,size='large' if task.startswith('L') else 'small',format=fmt,workflow=workflow,rep=rep,rc=rc,seconds=time.monotonic()-t,timeout=timeout,tool_calls=calls,tool_types=[i.get('type') for i in toolitems],compliant=compliant and not mutated and literal_valid,literal_valid=literal_valid,mutated=mutated,status=status,passed=g.returncode==0,input=usage.get('input_tokens'),cached=usage.get('cached_input_tokens'),output=usage.get('output_tokens'),turns=len(turns))
    row['total']=row['input']+row['output'] if row['input'] is not None and row['output'] is not None else None
    (dest/'result.json').write_text(json.dumps(row,indent=2)); print(ident,status,calls,row['output'],flush=True)
    return row
if __name__=='__main__':
    rnd=int(sys.argv[1]); tasks=fixtures(rnd)
    jobs=[(rnd,t,f,w,r) for t in tasks for f in FMT for w in ['on','off'] for r in [1,2]]
    random.Random(1800+rnd).shuffle(jobs)
    (E/f'round{rnd}_jobs.json').write_text(json.dumps(jobs,indent=2))
    with cf.ThreadPoolExecutor(max_workers=3) as pool: rows=list(pool.map(run,jobs))
    (E/f'round{rnd}.json').write_text(json.dumps(rows,indent=2))
