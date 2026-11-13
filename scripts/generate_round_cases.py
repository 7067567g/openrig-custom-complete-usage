#!/usr/bin/env python3
"""Generate synthetic-but-real 12-round workflow-group cases for the public examples.

The content is fictional and sanitized; every round is produced by the real
`wf.py` commands (new-run / append-status / state / new-round), then exported.
"""
from __future__ import annotations
import json, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / "scripts" / "wf.py"
OUT = ROOT / "examples" / "round-cases"

CASES = [
    ("case-12-rounds-hardening", "Harden a small service over 12 rounds",
     ["stabilize input validation", "add retry/backoff", "tighten evidence capture",
      "reduce flaky tests", "document failure modes", "add rollback drill",
      "review scope boundaries", "harden CI gate", "compress duplicated checks",
      "verify idempotency", "run close lint", "write final handoff"]),
    ("case-12-rounds-release", "Prepare a release over 12 rounds",
     ["freeze scope", "verify version consistency", "audit docs links",
      "run example demo", "run sanitization scan", "verify OpenRig render",
      "verify bridge doctor", "review release notes", "check CI matrix",
      "prepare tag checklist", "run final smoke", "close release case"]),
    ("case-12-rounds-docs", "Improve bilingual docs over 12 rounds",
     ["inventory EN/ZH pairs", "fix quickstart", "fix architecture",
      "fix multi-round guide", "fix OpenRig guide", "fix publishing policy",
      "add concepts glossary", "add examples index", "check link integrity",
      "review sanitization wording", "update validation report", "close docs case"]),
]

def call(*args: str) -> None:
    p = subprocess.run([sys.executable, str(WF), *args], cwd=ROOT, capture_output=True, text=True)
    if p.returncode != 0:
        print(p.stdout, p.stderr, sep="\n")
        raise SystemExit(p.returncode)

def append_decision(dec: Path, n: int, theme: str) -> None:
    text = dec.read_text(encoding="utf-8")
    marker = "## 2. 待决清单"
    block = f"""### D-{100+n}（Round {n}）{theme}

- **决策**：Round {n} 按计划完成；证据写入 `STATUS-Round-{n}.md`。
- **状态**：生效

"""
    if marker in text:
        text = text.replace(marker, block + marker, 1)
    else:
        text += "\n" + block
    dec.write_text(text, encoding="utf-8")

def generate(case_id: str, goal: str, steps: list[str]) -> None:
    run = ROOT / "runs" / case_id
    shutil.rmtree(run, ignore_errors=True)
    call("new-run", case_id, "--template", "templates/specialized/openrig-workflow-master",
         "--goal", goal, "--project-root", str(ROOT), "--scope", f"runs/{case_id}/**",
         "--tdo", "1", "--force")
    rounds = []
    for n, step in enumerate(steps, 1):
        call("append-status", case_id, "--agent", "tdo-a1", "--ws", "WS-1",
             "--action", f"R{n}: {step}", "--evidence", f"evidence/round-{n}.log", "--no-commit")
        call("state", case_id, "STATUS", "qa-pending", "--by", "main")
        call("state", case_id, "STATUS", "qa-done", "--by", "qa")
        rounds.append({"round": n, "action": step, "evidence": f"evidence/round-{n}.log", "verdict": "PASS"})
        if n < len(steps):
            call("new-round", case_id)
    dec = run / "DECISIONS.md"
    text = dec.read_text(encoding="utf-8")
    blocks = []
    for n, step in enumerate(steps, 1):
        blocks.append(f"### D-{100+n}（Round {n}）{step}\n\n- **决策**：Round {n} 按计划完成；证据写入 `STATUS-Round-{n}.md`。\n- 状态：生效\n")
    blocks.append(f"### D-999（Final）{case_id} 收口\n\n- **决策**：12 轮全部完成，QA 无阻塞项，证据见 `ROUNDS.md`。\n- 状态：达成\n")
    marker = "## 2. 待决清单"
    if marker in text:
        text = text.replace(marker, "\n".join(blocks) + "\n" + marker, 1)
    else:
        text += "\n" + "\n".join(blocks)
    dec.write_text(text, encoding="utf-8")
    proj = run / "PROJECT.md"
    ptext = proj.read_text(encoding="utf-8")
    report = """## 6. PMO 上报区

- **本轮结论**：12 轮全部完成；每轮 STATUS 为 qa-done，QA 无阻塞项，证据指针写入 `ROUNDS.md` 与 `evidence/round-N.log`。
- **待拍板**：无；建议 MAIN 接受收口，并关闭 PROJECT / STATUS / DECISIONS。
- **指标变化**：12/12 轮有证据指针；12/12 条决策已登记；0 个 open S1/S2；0 个阻塞项。
- **优化建议**：保留每轮证据日志、ROUNDS.json 与 DECISIONS 切片，作为后续真实项目的复用模板；下一批案例可加入真实模型调用与 token/成本记录。
- **风险提示**：这是合成案例，不代表真实项目结果；只证明 workflow-group 的 12 轮状态机与文档合同可以完整跑通。

"""
    import re as _re
    ptext = _re.sub(r"## 6\. PMO 上报区.*?(?=\n## 7\.)", report, ptext, flags=_re.S)
    proj.write_text(ptext, encoding="utf-8")
    call("state", case_id, "PROJECT", "plan-ready", "--by", "pmo")
    call("state", case_id, "PROJECT", "waiting-main", "--by", "pmo")
    call("state", case_id, "PROJECT", "closed", "--by", "main")
    call("state", case_id, "DECISIONS", "closed", "--by", "main")
    call("state", case_id, "STATUS", "closed", "--by", "main")
    (run / "ROUNDS.json").write_text(json.dumps({"case": case_id, "goal": goal, "rounds": rounds}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = ["# ROUNDS — " + case_id, "", "| round | action | evidence | verdict |", "|---:|---|---|---|"]
    md += [f"| {r['round']} | {r['action']} | {r['evidence']} | {r['verdict']} |" for r in rounds]
    (run / "ROUNDS.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (run / "evidence").mkdir(exist_ok=True)
    for r in rounds:
        (run / "evidence" / f"round-{r['round']}.log").write_text(f"round {r['round']}: {r['action']}\nverdict: PASS\n", encoding="utf-8")
    # export sanitized
    dst = OUT / case_id
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(run, dst / "run", ignore=shutil.ignore_patterns(".locks", "_run", "work"))
    for p in (dst / "run").rglob("*"):
        if not p.is_file() or p.suffix in {".xlsx", ".pyc"}:
            continue
        try: s = p.read_text(encoding="utf-8")
        except UnicodeDecodeError: continue
        s = s.replace(str(ROOT), "<repo-root>").replace(f"/tmp/openrig-workflow-{case_id}", "<openrig-home>")
        p.write_text(s, encoding="utf-8")
    # xlsx -> readable summary
    (dst / "run" / "ISSUES.md").write_text("# ISSUES — " + case_id + "\n\nNo open blocking issues; all QA passes recorded in ROUNDS.md.\n", encoding="utf-8")
    (dst / "README.md").write_text(f"""**English** | [简体中文](README.zh-CN.md)

# {case_id}

A synthetic but real 12-round workflow-group case: **{goal}**.

- generated by `scripts/generate_round_cases.py`
- every round ran `wf.py append-status`, `state`, and `new-round`
- 12 status files, 12 decisions, `ROUNDS.md`, `ROUNDS.json`, evidence logs
- sanitized: no personal paths, secrets, or real project data
""", encoding="utf-8")
    (dst / "README.zh-CN.md").write_text(f"""[English](README.md) | **简体中文**

# {case_id}

一个合成但真实的 12 轮 workflow-group 案例：**{goal}**。

- 由 `scripts/generate_round_cases.py` 生成
- 每轮真实执行 `wf.py append-status`、`state`、`new-round`
- 包含 12 个 STATUS、12 条决策、`ROUNDS.md`、`ROUNDS.json`、证据日志
- 已脱敏：无个人路径、密钥、真实项目数据
""", encoding="utf-8")
    shutil.rmtree(run, ignore_errors=True)
    print(f"[OK] {case_id}: {len(rounds)} rounds -> {dst}")

def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for case_id, goal, steps in CASES:
        generate(case_id, goal, steps)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
