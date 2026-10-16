"""Re-grade every no-tool answer offline from the raw stream (result text), so grading doesn't depend on
the live check. Writes results/graded.csv with the apply status per run."""
import csv, json, os, shutil, subprocess, tempfile, sys
E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = "/workspace/work/tig/_harness/fixtures/SUITE14"
rows = list(csv.DictReader(open(f"{E}/results/runs.csv"))); out = []
for r in rows:
    st = ""
    if r["cond"] != "tool":
        res = [d for d in (json.loads(l) for l in open(f"{E}/{r['raw_jsonl']}") if l.strip()) if d.get("type") == "result"]
        txt = res[-1].get("result", "") if res else ""
        w = tempfile.mkdtemp(); shutil.copytree(f"{S}/{r['task']}", w, dirs_exist_ok=True)
        open(f"{w}/.claude_answer.txt", "w").write(txt)
        env = dict(os.environ); 
        subprocess.run(["python3", f"{E}/scripts/apply.py", r["cond"]], cwd=w, capture_output=True)
        st = open(f"{w}/.apply_status").read(); shutil.rmtree(w)
        st = st if not os.path.exists(f"{E}/results/.mode") else st
    else:
        st = "ok" if r["passed"] == "True" else "test_fail"
    r["status"] = st; out.append(r)
w = csv.DictWriter(open(f"{E}/results/graded.csv", "w"), fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
for r in out: print(r["cond"], r["task"], r["passed"], r["status"], r["output_tokens"])
