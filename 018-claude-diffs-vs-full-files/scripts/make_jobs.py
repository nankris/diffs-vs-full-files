import os
E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = "/workspace/work/tig/_harness/fixtures/SUITE14"
PK = ["N01_median","N02_duration","N03_csv","T02_duplicate","T05_stale","T06_neardup","T07_multihunk","T08_insert","T09_delete","T10_replace_all"]
INSTR = {
 "tool": "Fix the bug by editing broken.js in the current directory with your file-editing tools, then stop. Don't run anything else and don't edit test.js.",
 "full": "Do not use any tools. Reply with the complete corrected contents of broken.js in a single ```js code block, and nothing else.",
 "udiff": "Do not use any tools. Reply with only a unified diff (--- broken.js / +++ broken.js headers, @@ hunks) that fixes broken.js, in a single ```diff code block, and nothing else.",
 "json": "Do not use any tools. Reply with only a JSON array of exact search/replace edits for broken.js, like [{\"old\": \"exact existing text\", \"new\": \"replacement\"}], in a single ```json code block, and nothing else. Each \"old\" must appear exactly once in the file.",
}
jobs = []
for pkg in PK:
    files = "".join(f"\n`{f}`:\n```\n{open(f'{S}/{pkg}/{f}').read()}```\n" for f in sorted(os.listdir(f"{S}/{pkg}")))
    for arm, ins in INSTR.items():
        p = f"`node test.js` fails. Make it pass by fixing broken.js (never edit test.js). Files:\n{files}\n{ins}"
        pf = f"{E}/scripts/prompts/{arm}__{pkg}.txt"; open(pf, "w").write(p)
        fl = "" if arm == "tool" else "--flag=--tools --flag=''"
        jobs.append(f"--exp {E} --cond {arm} --task {S}/{pkg} --rep 1 --timeout 300 --check 'python3 {E}/scripts/apply.py {arm}' "
                    f"--flag=--disable-slash-commands {fl} --prompt \"$(cat {pf})\"")
open(f"{E}/scripts/jobs.txt", "w").write("\n".join(jobs) + "\n"); print(len(jobs))
