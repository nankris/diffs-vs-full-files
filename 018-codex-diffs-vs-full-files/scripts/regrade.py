"""Re-grade every no-tool answer offline from the raw `codex exec --json` stream (last agent_message),
in a fresh copy of the fixture, with scripts/apply.py. Tool-arm rows keep the live grade. -> results/graded.csv"""
import csv, json, os, shutil, subprocess, tempfile
E = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); S = f"{E}/scripts/harness/fixtures/SUITE14"
out = []
for r in csv.DictReader(open(f"{E}/results/runs.csv")):
    ans = ""
    for l in open(os.path.join(E, r["raw_jsonl"])):
        it = json.loads(l).get("item") or {}
        if it.get("type") == "agent_message": ans = it.get("text", "")
    status = "ok" if r["passed"] == "1" else "test_fail"
    if r["cond"] != "tool":
        d = tempfile.mkdtemp(); shutil.copytree(f"{S}/{r['task']}", d, dirs_exist_ok=True)
        open(f"{d}/.codex_answer.txt", "w").write(ans)
        env = dict(os.environ, APPLY_LOG="/dev/null")
        subprocess.run(["python3", f"{E}/scripts/apply.py", r["cond"]], cwd=d, capture_output=True, env=env)
        status = open(f"{d}/.apply_status").read().strip()
        shutil.rmtree(d)
    out.append(dict(task=r["task"], fmt=r["cond"], status=status, passed=int(status in ("ok", "ok_recount")),
                    output_tokens=r["output_tokens"], reasoning_output_tokens=r["reasoning_output_tokens"],
                    answer_chars=len(ans), total_tokens=r["total_tokens"], input_tokens=r["input_tokens"],
                    cached_input_tokens=r["cached_input_tokens"], model_calls=r["model_calls"], tool_calls=r["tool_calls"],
                    est_cost_usd=r["est_cost_usd"], wall_s=r["wall_s"]))
with open(f"{E}/results/graded.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
print({s: sum(o["status"] == s for o in out) for s in sorted({o["status"] for o in out})})
