#!/usr/bin/env python3
"""apply.py MODE : apply the model's text answer (.codex_answer.txt) to broken.js, then run node test.js.
MODE: tool (nothing to apply; the agent edited the file itself) | full (one ```js block = whole new file)
      | udiff (unified diff applied with `patch`) | json (JSON list of {"old":..,"new":..} exact replacements)
Exit 0 = test passes. Writes .apply_status: ok | parse_error | apply_error | test_fail"""
import sys, re, json, subprocess, os
mode = sys.argv[1]; ans = open(".codex_answer.txt").read() if os.path.exists(".codex_answer.txt") else ""
LOG = os.environ.get("APPLY_LOG") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "apply_log.csv")
def done(st, rc):
    import hashlib, time
    open(".apply_status", "w").write(st)
    h = hashlib.md5(open("test.js","rb").read()).hexdigest()[:8]
    with open(LOG, "a") as f: f.write(f"{int(time.time())},{mode},{h},{st}\n")
    sys.exit(rc)
def block(lang=None):
    m = re.findall(r"```[a-zA-Z]*\n(.*?)```", ans, re.S)
    return m
try:
    if mode == "full":
        b = block()
        if not b: done("parse_error", 2)
        open("broken.js", "w").write(b[0] if b[0].endswith("\n") else b[0] + "\n")
    elif mode == "udiff":
        b = block(); d = b[0] if b else ans
        open(".ans.diff", "w").write(d if d.endswith("\n") else d + "\n")
        # `patch` isn't installed in this sandbox; use git apply. Strict first, then --recount (fixes wrong hunk line counts).
        r = subprocess.run("git apply -p0 .ans.diff || git apply -p1 .ans.diff", shell=True, capture_output=True)
        if r.returncode != 0:
            r = subprocess.run("git apply -p0 --recount .ans.diff || git apply -p1 --recount .ans.diff", shell=True, capture_output=True)
            if r.returncode == 0: mode = "udiff_recount"
        if r.returncode != 0:
            done("apply_error", 3)
    elif mode == "json":
        b = block(); t = b[0] if b else ans
        t = t[t.find("["): t.rfind("]") + 1]
        try: edits = json.loads(t)
        except Exception: done("parse_error", 2)
        src = open("broken.js").read()
        for e in edits:
            if e["old"] not in src or src.count(e["old"]) != 1: done("apply_error", 3)
            src = src.replace(e["old"], e["new"], 1)
        open("broken.js", "w").write(src)
except SystemExit: raise
except Exception: done("apply_error", 3)
r = subprocess.run(["node", "test.js"], capture_output=True, timeout=60)
done(("ok" if mode != "udiff_recount" else "ok_recount") if r.returncode == 0 else "test_fail", 0 if r.returncode == 0 else 1)
