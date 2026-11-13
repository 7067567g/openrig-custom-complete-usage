#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wf.py — 工作流组编排器（单一入口）

子命令:
  new-run <run-id> --goal "..." [--project-name ...] [--tdo N] [--force]
  new-round <run-id>                  # 生成下一轮 STATUS，PROJECT 回到 pmo-plan
  state <run-id> <PROJECT|DECISIONS|STATUS> <new-state>
  brief --role pmo|tdo|qa|safety --run <run-id> [--agent 名字]
  lock <run-id> --agent 名字 [--wait 秒] [--steal]
  unlock <run-id> [--agent 名字] [--force]
  lock-status <run-id>
  append-status <run-id> --agent 名字 --ws WS-1 --action "..." --evidence "..." [--state 进行中|完成|阻塞] [--blocker "..."] [--also 路径]... [--no-commit]
  doctor <run-id> [--json]

退出码: 0 正常 / 1 契约错误 / 2 用法错误 / 3 依赖缺失 / 4 锁失败
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from adapters import headless as headless_adapter

ROOT = Path(__file__).resolve().parent.parent  # workflow-group/
REPO = ROOT.parent  # KB 仓库根
TEMPLATES = ROOT / "templates"
RUNS = ROOT / "runs"
LOCK_TTL = 900  # 秒；超时可 --steal 接管
LOCK_RETRY = 3
LOCK_WAIT = 60  # 默认最大等待秒数（高并行下更稳）
DOC_ALLOWED = {
    "PROJECT": ["pmo-plan", "plan-ready", "waiting-main", "closed"],
    "DECISIONS": ["open", "closed"],
    "STATUS": ["tdo-pending", "tdo-in-progress", "qa-pending", "qa-done", "closed"],
}
DOC_OWNER = {"PROJECT": "PMO", "DECISIONS": "主会话", "STATUS": "TDO"}
STATE_TRANSITIONS = {
    ("PROJECT", "pmo-plan", "plan-ready"): {"PMO"},
    ("STATUS", "tdo-pending", "tdo-in-progress"): {"TDO"},
    ("STATUS", "tdo-in-progress", "qa-pending"): {"MAIN", "主会话"},
    ("STATUS", "qa-pending", "qa-done"): {"QA"},
    ("PROJECT", "plan-ready", "waiting-main"): {"PMO"},
    ("PROJECT", "waiting-main", "closed"): {"MAIN", "主会话"},
    ("DECISIONS", "open", "closed"): {"MAIN", "主会话"},
    ("STATUS", "qa-done", "closed"): {"MAIN", "主会话"},
}
ROLE_ALIASES = {
    "main": "MAIN", "MAIN": "MAIN", "主会话": "MAIN",
    "pmo": "PMO", "PMO": "PMO",
    "tdo": "TDO", "TDO": "TDO",
    "qa": "QA", "QA": "QA",
    "safety": "SAFETY", "SAFETY": "SAFETY",
}
HEADER_RE = re.compile(r"<!-- wf-doc\n(.*?)\n-->", re.S)
ROUND_PLAN_BLOCK_RE = re.compile(r"<!-- wf:round-plan\n(.*?)\n-->", re.S)
VERDICT_BLOCK_RE = re.compile(r"<!-- wf:verdict\n(.*?)\n-->", re.S)
PLACEHOLDER_RE = re.compile(r"<(?![!/])[^<>\n]*[\w\u4e00-\u9fff][^<>\n]*>")
_URL_CHARS = ("://",)
RUN_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


# ------------------------------------------------------------------ utils
def die(msg, code=1):
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(code)


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def today():
    return datetime.now().strftime("%Y-%m-%d")


def run_dir(run_id):
    p = RUNS / run_id
    if not p.exists():
        die(f"run 不存在: {p}")
    return p


def status_files(run):
    files = []
    for p in run.glob("STATUS-Round-*.md"):
        m = re.search(r"STATUS-Round-(\d+)\.md$", p.name)
        if m:
            files.append((int(m.group(1)), p))
    files.sort()
    return files


def latest_status(run, required=True):
    files = status_files(run)
    if not files:
        if required:
            die(f"{run} 下没有 STATUS-Round-*.md（先 new-run 或 new-round）")
        return None
    return files[-1][1]


def doc_path(run, doc):
    if doc == "STATUS":
        return latest_status(run)
    return run / f"{doc}.md"


def read_header(p):
    try:
        text = p.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    m = HEADER_RE.search(text)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def write_header_field(p, key, value):
    text = p.read_text(encoding="utf-8")
    m = HEADER_RE.search(text)
    if not m:
        die(f"{p} 缺少 <!-- wf-doc --> 元信息块")
    block = m.group(0)
    lines = block.splitlines()
    body, tail = lines[1:-1], lines[-1]  # 首行 <!-- wf-doc，末行 -->
    found = False
    for i, line in enumerate(body):
        if line.strip().startswith(key + ":"):
            body[i] = f"{key}: {value}"
            found = True
            break
    if not found:
        body.append(f"{key}: {value}")
    new_block = "\n".join([lines[0]] + body + [tail])
    p.write_text(text[: m.start()] + new_block + text[m.end() :], encoding="utf-8")


def find_placeholders(text):
    """只找真正的待填占位符：排除 HTML 注释、闭合标签、URL、纯符号。"""
    out = []
    for m in PLACEHOLDER_RE.finditer(text):
        if any(c in m.group(0) for c in _URL_CHARS):
            continue
        out.append(m)
    return out


def _spec_declarations(path):
    """Read machine-readable §0 baseline/contracts declarations from SPEC.md."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return {"baseline": "", "contracts": ""}
    out = {}
    for key in ("baseline", "contracts"):
        m = re.search(rf"^{key}:\s*(.+)$", text, re.M)
        out[key] = m.group(1).strip() if m else ""
    return out


def _template_wf_metadata(tpl):
    """Derive wf-doc metadata from a template's SPEC §0 and baseline registry."""
    tpl = Path(tpl)
    name = tpl.name or "generic"
    decl = _spec_declarations(tpl / "SPEC.md")
    baseline = decl["baseline"]
    contracts = decl["contracts"]
    tags = [f"template/{name}"]
    primary_type = "generic"
    maturity = "unassessed"
    if baseline.startswith("composite/"):
        base_ref = baseline.split()[0]
        base_id = base_ref.split("@", 1)[0].split("/", 1)[1]
        primary_type = f"composite/{base_id}"
        tags.append(f"baseline/{base_id}")
        try:
            registry = json.loads(
                (TEMPLATES / "baseline" / "REGISTRY.json").read_text(encoding="utf-8")
            )
            item = next(
                (x for x in registry.get("baselines", []) if x.get("id") == base_id),
                None,
            )
            if item:
                maturity = item.get("maturity") or maturity
        except Exception:
            pass
    elif baseline.startswith("none"):
        primary_type = "atomic-composition"
        tags.append("baseline/none")
    return {
        "tags": ", ".join(tags),
        "primary_type": primary_type,
        "maturity": maturity,
        "baseline": baseline or "none — generic four-piece",
        "contracts": contracts or "none",
    }


def _extract_hidden_block(path, regex):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    m = regex.search(text)
    return m.group(1).strip() + "\n" if m else ""


def sync_round_plan(rd):
    """Project a hidden wf:round-plan block from PROJECT into ROUND-PLAN.md."""
    body = _extract_hidden_block(rd / "PROJECT.md", ROUND_PLAN_BLOCK_RE)
    if not body:
        return None
    out = rd / "ROUND-PLAN.md"
    out.write_text("# ROUND-PLAN\n\n" + body, encoding="utf-8")
    return out


def sync_verdict(rd):
    """Project a hidden wf:verdict block from DECISIONS into reports/VERDICT.md."""
    body = _extract_hidden_block(rd / "DECISIONS.md", VERDICT_BLOCK_RE)
    if not body:
        return None
    out = rd / "reports" / "VERDICT.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("# VERDICT\n\n" + body, encoding="utf-8")
    return out


def section(text, start_marker, end_marker=None):
    i = text.find(start_marker)
    if i < 0:
        return ""
    i += len(start_marker)
    j = text.find(end_marker, i) if end_marker else len(text)
    if j < 0:
        j = len(text)
    return text[i:j].strip()


# ---------------------------------------------------- S-3 per-WS 交接槽
HANDOFF_WS_RE = re.compile(
    r"(<!-- wf:handoff-ws:start -->)(.*?)(<!-- wf:handoff-ws:end -->)", re.S
)


def fill_handoff_slots(text, n):
    """把 STATUS 模板的 per-WS 交接槽填成 n 条（S-3）。

    仅替换 `<!-- wf:handoff-ws:start/end -->` 之间的内容；模板若无该标记则原样返回
    （向后兼容：旧模板/自定义模板仍可用，不报错）。n 至少为 1。
    """
    try:
        count = max(1, int(n))
    except (TypeError, ValueError):
        count = 1
    if "<!-- wf:handoff-ws:start -->" not in text:
        return text
    body = "\n".join(f"  - **WS-{i}**：" for i in range(1, count + 1))

    def _rep(m):
        return f"{m.group(1)}\n{body}\n{m.group(3)}"

    return HANDOFF_WS_RE.sub(_rep, text, count=1)


def max_ws_in_statuses(rd):
    """从既有 STATUS 进度表推断 WS 数量（用于 new-round 预填交接槽）。"""
    mx = 1
    for _, p in status_files(rd):
        for m in re.finditer(r"\bWS-(\d+)\b", p.read_text(encoding="utf-8")):
            mx = max(mx, int(m.group(1)))
    return mx


# ------------------------------------------------------------------ lock
def lock_path(run):
    return run / ".locks" / "status.lock"


def read_lock(run):
    lp = lock_path(run)
    if not lp.exists():
        return None
    try:
        meta = json.loads((lp / "meta.json").read_text(encoding="utf-8"))
    except Exception:
        meta = {}
    age = time.time() - lp.stat().st_mtime
    meta["age"] = int(age)
    meta["stale"] = age > LOCK_TTL
    return meta


def acquire_lock(run, agent, wait=LOCK_WAIT, steal=False):
    lp = lock_path(run)
    lp.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + max(0, wait)
    attempt = 0
    while True:
        try:
            os.mkdir(lp)
            (lp / "meta.json").write_text(
                json.dumps(
                    {
                        "agent": agent,
                        "pid": os.getpid(),
                        "at": now_str(),
                        "acquired_ts": time.time(),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            return True
        except FileExistsError:
            meta = read_lock(run) or {}
            if steal and meta.get("stale"):
                bak = lp.with_name(f"status.lock.steal.{int(time.time())}")
                try:
                    os.rename(lp, bak)
                except OSError:
                    pass
                append_steal_note(run, agent, meta)
                continue
            if time.time() >= deadline:
                who = meta.get("agent", "?")
                age = meta.get("age", "?")
                tag = "（已过期，可 --steal 接管）" if meta.get("stale") else ""
                print(f"[LOCK] 被 {who} 持有，已等 {age}s{tag}", file=sys.stderr)
                return False
            attempt += 1
            time.sleep(min(2**attempt, 8))


def release_lock(run, agent=None, force=False):
    lp = lock_path(run)
    if not lp.exists():
        print("[LOCK] 本无锁")
        return True
    meta = read_lock(run) or {}
    if agent and meta.get("agent") and meta["agent"] != agent and not force:
        die(f"锁属于 {meta['agent']}，不是 {agent}（要强解加 --force）")
    shutil.rmtree(lp, ignore_errors=True)
    return True


def append_steal_note(run, agent, old_meta):
    st = latest_status(run, required=False)
    if not st:
        return
    text = st.read_text(encoding="utf-8")
    row = (
        f"| {now_str()} | {agent} | - | 接管过期锁 | 原持有者 "
        f"{old_meta.get('agent', '?')}，锁龄 {old_meta.get('age', '?')}s | steal |\n"
    )
    text = text.replace("<!-- wf:progress:end -->", row + "<!-- wf:progress:end -->")
    st.write_text(text, encoding="utf-8")


# ------------------------------------------------------------------ git
def _normalize_also_arg(raw):
    """Normalize a TDO `--also` path without changing its tracked meaning.

    F9 follow-up: when the CLI runs from workflow-group/ and the caller passes a
    path already prefixed with `workflow-group/`, resolve it against the repo
    root instead of producing `workflow-group/workflow-group/...`. Absolute
    paths and ordinary relative paths keep their existing semantics.
    """
    p = Path(raw)
    if p.is_absolute():
        return p
    cwd = Path.cwd().resolve()
    root = ROOT.resolve()
    if cwd == root and p.parts and p.parts[0] == root.name:
        candidate = (root / Path(*p.parts[1:])).resolve()
        if candidate.exists():
            return candidate
    return (cwd / p).resolve()


def _git_rel(paths):
    rel = []
    for p in paths:
        try:
            rel.append(str(Path(p).resolve().relative_to(REPO)))
        except ValueError:
            rel.append(str(p))
    return rel


def _gitignored(rel):
    """挑出被 .gitignore 忽略且尚未跟踪的路径。

    这类路径不能交给 `git add`：git 会返回非 0，导致 `--also` 整条提交失败
    （F9 事故：进度行已落盘但没入库）。已跟踪文件即便命中忽略规则也照常处理。
    """
    ignored = []
    for r in rel:
        c = subprocess.run(
            ["git", "-C", str(REPO), "check-ignore", "--quiet", "--", r],
            capture_output=True,
            text=True,
        )
        if c.returncode != 0:
            continue
        t = subprocess.run(
            ["git", "-C", str(REPO), "ls-files", "--error-unmatch", "--", r],
            capture_output=True,
            text=True,
        )
        if t.returncode != 0:
            ignored.append(r)
    return ignored


def git_commit(paths, message):
    rel = _git_rel(paths)
    skipped = _gitignored(rel)
    if skipped:
        print(
            "[WARN] 跳过被 .gitignore 忽略的路径（否则 git add 会整条失败）："
            + ", ".join(skipped),
            file=sys.stderr,
        )
    keep = [r for r in rel if r not in skipped]
    if not keep:
        return False, "所有路径都被 .gitignore 忽略，无可提交内容"
    try:
        r1 = subprocess.run(
            ["git", "-C", str(REPO), "add", "--"] + keep, capture_output=True, text=True
        )
        if r1.returncode != 0:
            return False, (r1.stdout + r1.stderr).strip()
        r2 = subprocess.run(
            ["git", "-C", str(REPO), "commit", "-m", message],
            capture_output=True,
            text=True,
        )
        if r2.returncode != 0:
            return False, (r2.stdout + r2.stderr).strip()
        return True, r2.stdout.strip()
    except Exception as e:  # git 不存在等
        return False, str(e)


# ------------------------------------------------------------------ new-run
def cmd_new_run(args):
    rid = args.run_id
    if not RUN_ID_RE.match(rid):
        die("run-id 必须是小写 kebab-case（[a-z0-9][a-z0-9-]*）")
    rd = RUNS / rid
    if rd.exists() and not args.force:
        die(f"{rd} 已存在；重建加 --force（会覆盖四件套）")
    rd.mkdir(parents=True, exist_ok=True)
    (rd / ".locks").mkdir(exist_ok=True)

    name = args.project_name or rid
    tdo = str(args.tdo)
    tpl = Path(args.template) if args.template else TEMPLATES
    if not tpl.is_dir():
        die(f"模板目录不存在: {tpl}")
    def _is_under(path: Path, parent: Path) -> bool:
        try:
            path.relative_to(parent)
            return True
        except ValueError:
            return False

    resolved_tpl = tpl.resolve()
    frozen_dirs = ((TEMPLATES / "contracts").resolve(), (TEMPLATES / "baseline").resolve())
    if any(resolved_tpl == d or _is_under(resolved_tpl, d) for d in frozen_dirs):
        die(
            "templates/contracts/* 与 templates/baseline/* 是冻结原子轮型/基准参考，"
            "不能直接实例化；请改用 templates/specialized/<name>，并在 SPEC.md §0 写 "
            "baseline: composite/<name>@<version> 与 contracts: <type>@<version>,..."
        )
    goal = args.goal
    if args.goal_file:
        goal = Path(args.goal_file).read_text(encoding="utf-8").strip()
    goal = re.sub(r"\s*\n\s*", " / ", goal) if goal else goal  # 表格单元格不能多行
    repl = {
        "<RUN-ID>": rid,
        "<PROJECT-NAME>": name,
        "<GOAL>": goal or "<填一句话目标>",
        "<PROJECT-ROOT>": args.project_root or "<填项目根路径>",
        "<WRITE-SCOPE>": args.scope or "<填写权限白名单（相对项目仓根）>",
        "<DATE>": today(),
        "<ROUND-N>": "1",
        "<TDO-N>": tdo,
        "<N'>": tdo,
    }

    def pick(name):
        return (tpl / name) if (tpl / name).exists() else (TEMPLATES / name)

    def inst(src, dst):
        text = pick(src).read_text(encoding="utf-8")
        for k, v in repl.items():
            text = text.replace(k, v)
        (rd / dst).write_text(text, encoding="utf-8")

    inst("PROJECT.md", "PROJECT.md")
    meta = _template_wf_metadata(tpl)
    for key, value in meta.items():
        write_header_field(rd / "PROJECT.md", key, value)
    inst("DECISIONS.md", "DECISIONS.md")
    inst("STATUS-Round-n.md", "STATUS-Round-1.md")
    # S-3：按 TDO 数预填 per-WS 交接小节（模板无该槽时自动跳过，向后兼容）
    st1 = rd / "STATUS-Round-1.md"
    st1.write_text(
        fill_handoff_slots(st1.read_text(encoding="utf-8"), args.tdo),
        encoding="utf-8",
    )
    shutil.copyfile(pick("ISSUES.xlsx"), rd / "ISSUES.xlsx")
    if (tpl / "SPEC.md").exists():
        shutil.copyfile(tpl / "SPEC.md", rd / "SPEC.md")
    print(f"[OK] run 已建立: {rd}（模板: {tpl}）")
    extra = " + SPEC.md" if (rd / "SPEC.md").exists() else ""
    print(
        f"     PROJECT.md / DECISIONS.md / STATUS-Round-1.md / ISSUES.xlsx{extra} + .locks/"
    )
    print("下一步（主会话）:")
    print(f"  1) 确认 PROJECT.md §0/§1 目标与终止判据（占位符 <...> 要填掉）")
    print(f"  2) python3 scripts/wf.py brief --role pmo --run {rid}  → 贴给 PMO 会话")
    print(f"  3) 随时体检: python3 scripts/wf.py doctor {rid}")


# ------------------------------------------------------------------ new-round
def cmd_new_round(args):
    rd = run_dir(args.run_id)
    files = status_files(rd)
    n = files[-1][0] + 1 if files else 1
    dst = rd / f"STATUS-Round-{n}.md"
    if dst.exists():
        die(f"{dst} 已存在")
    text = (TEMPLATES / "STATUS-Round-n.md").read_text(encoding="utf-8")
    proj = rd / "PROJECT.md"
    name = read_header(proj).get("run", args.run_id)
    # 项目名从 H1 取，退化用 run-id
    m = re.search(r"^# PROJECT — (.+)$", proj.read_text(encoding="utf-8"), re.M)
    if m:
        name = m.group(1).strip()
    repl = {
        "<RUN-ID>": args.run_id,
        "<PROJECT-NAME>": name,
        "<ROUND-N>": str(n),
        "<DATE>": today(),
    }
    for k, v in repl.items():
        text = text.replace(k, v)
    # S-3：按既有 STATUS 里的 WS 数预填交接小节（无槽/无历史时退化为 1）
    text = fill_handoff_slots(text, max_ws_in_statuses(rd))
    dst.write_text(text, encoding="utf-8")
    write_header_field(proj, "round", str(n))
    write_header_field(proj, "state", "pmo-plan")
    write_header_field(proj, "updated", today())
    dec = rd / "DECISIONS.md"
    if dec.exists():
        write_header_field(dec, "round", str(n))
        write_header_field(dec, "updated", today())
    print(f"[OK] 新轮已建立: {dst}")
    print(f"     PROJECT.md → state=pmo-plan, round={n}")
    print(
        "下一步: 用 brief --role pmo 发计划委派；TDO 完成后 append-status 写的就是这一轮。"
    )


# ------------------------------------------------------------------ contracts sync
def cmd_sync_contracts(args):
    rd = run_dir(args.run_id)
    plan = sync_round_plan(rd)
    verdict = sync_verdict(rd)
    if plan is None and verdict is None:
        die("PROJECT.md 无 wf:round-plan 块，DECISIONS.md 无 wf:verdict 块")
    if plan is not None:
        print(f"[OK] ROUND-PLAN: {plan.relative_to(ROOT)}")
    if verdict is not None:
        print(f"[OK] VERDICT: {verdict.relative_to(ROOT)}")


# ------------------------------------------------------------------ state
def _closure_issue_blockers(rd):
    """Return open S1/S2 rows that must block waiting-main/closed."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import issues as issues_mod

        rows = issues_mod.read_rows(rd / "ISSUES.xlsx")
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        return [f"ISSUES 读取失败，无法执行关闭收口: {exc}"]
    blockers = []
    for row in rows:
        if row.get("严重度") in ("S1", "S2") and row.get("状态") not in ("已关闭", "挂起"):
            blockers.append(f"{row.get('ID')}: {row.get('严重度')} {row.get('标题')}")
    return blockers


def cmd_state(args):
    rd = run_dir(args.run_id)
    doc = args.doc.upper()
    if doc not in DOC_ALLOWED:
        die(f"doc 必须是 {list(DOC_ALLOWED)} 之一")
    if args.new_state not in DOC_ALLOWED[doc]:
        die(f"{doc} 状态非法: {args.new_state}；允许: {' / '.join(DOC_ALLOWED[doc])}")
    p = doc_path(rd, doc)
    old_state = read_header(p).get("state", "")
    transition = (doc, old_state, args.new_state)
    by_raw = getattr(args, "by", "") or ""
    if by_raw:
        by = ROLE_ALIASES.get(by_raw)
        if not by:
            die(f"--by 非法: {by_raw!r}；允许 MAIN/PMO/TDO/QA/SAFETY")
        allowed = STATE_TRANSITIONS.get(transition)
        if not allowed:
            die(f"未登记的状态迁移: {doc} {old_state}→{args.new_state}")
        if by not in allowed:
            die(
                f"身份越权: {doc} {old_state}→{args.new_state} 只能由 "
                f"{' / '.join(sorted(allowed))} 执行；收到 {by}"
            )
    elif transition in {
        ("PROJECT", "plan-ready", "waiting-main"),
        ("PROJECT", "waiting-main", "closed"),
        ("DECISIONS", "open", "closed"),
        ("STATUS", "qa-done", "closed"),
    }:
        die(
            "关键状态迁移必须提供 --by <MAIN|PMO|TDO|QA>，否则无法执行状态迁移身份门禁"
        )
    else:
        print(
            "[WARN] 未提供 --by：本次按兼容模式迁移，无法校验执行者身份",
            file=sys.stderr,
        )
    if doc == "PROJECT" and args.new_state == "plan-ready":
        proj_header = read_header(rd / "PROJECT.md")
        projected = sync_round_plan(rd)
        if proj_header.get("contract_mode") == "strict":
            if projected is None and not (rd / "ROUND-PLAN.md").is_file():
                die(
                    "contract_mode=strict：PROJECT.md 缺 wf:round-plan 块，"
                    "且 ROUND-PLAN.md 不存在；拒绝进入 plan-ready"
                )
            gate_errors, _, _ = _check_plan_gate(rd)
            if gate_errors:
                die("PLAN-GATE 未通过，拒绝进入 plan-ready：" + "；".join(gate_errors))
        elif projected is not None:
            gate_errors, _, _ = _check_plan_gate(rd)
            if gate_errors:
                print(
                    "[WARN] 已投影 ROUND-PLAN.md 但 PLAN-GATE 未全绿："
                    + "；".join(gate_errors),
                    file=sys.stderr,
                )
    if doc == "PROJECT" and args.new_state == "waiting-main":
        projected = sync_verdict(rd)
        if projected is not None:
            print(f"[OK] 已投影判词: {projected.relative_to(ROOT)}")
    if args.new_state in ("waiting-main", "closed"):
        rc = doctor(args.run_id, as_json=False)
        if rc != 0:
            die(f"doctor 未通过，拒绝迁移到 {args.new_state}")
        st_file = latest_status(rd, required=False)
        if st_file is not None and read_header(st_file).get("state") != "qa-done":
            die(
                f"关闭收口未通过：STATUS.state={read_header(st_file).get('state')}，"
                "要求 qa-done"
            )
        blockers = _closure_issue_blockers(rd)
        if blockers:
            die(
                f"关闭收口未通过：仍有 open S1/S2：{'；'.join(blockers)}"
            )
        if args.new_state == "closed":
            dec_text = (rd / "DECISIONS.md").read_text(encoding="utf-8")
            if not re.search(r"状态：\s*(达成|终止|关闭)", dec_text):
                die("关闭收口未通过：DECISIONS.md 缺“状态：达成/终止”的终止决策")
    write_header_field(p, "state", args.new_state)
    write_header_field(p, "updated", today())
    print(f"[OK] {p.name} → state={args.new_state}" + (f"（by={by_raw}）" if by_raw else ""))


# ------------------------------------------------------------------ append-status
def insert_before(text, marker, line):
    return text.replace(marker, line + marker)


def cmd_append_status(args):
    rd = run_dir(args.run_id)
    st = latest_status(rd)
    if not acquire_lock(rd, args.agent, wait=args.wait, steal=args.steal):
        die("拿不到 STATUS 锁，稍后重试（不要绕过锁写文件）", code=4)
    try:
        h = read_header(st)
        if h.get("state") == "tdo-pending":
            write_header_field(st, "state", "tdo-in-progress")
        if h.get("state") in ("qa-pending", "qa-done", "closed"):
            die(
                f"STATUS 当前 state={h.get('state')}，不应再写进度（本轮已交 QA/已关闭）"
            )
        if h.get("run") and h["run"] != args.run_id:
            die(f"STATUS 的 run 字段是 {h['run']}，与命令不符")
        state = args.state or "完成"
        if state not in ("进行中", "完成", "阻塞"):
            die("--state 只允许 进行中 / 完成 / 阻塞")
        if state == "阻塞" and not args.blocker:
            die("--state 阻塞 必须给 --blocker 描述")
        if not args.action.strip():
            die("--action 不能为空")
        if not args.evidence.strip():
            die("--evidence 不能为空（证据可复现是硬规则）")

        text = st.read_text(encoding="utf-8")
        row = (
            f"| {now_str()} | {args.agent} | {args.ws} | {args.action.strip()} | "
            f"{args.evidence.strip()} | {state} |\n"
        )
        if "<!-- wf:progress:end -->" not in text:
            die("STATUS 缺少 <!-- wf:progress:end --> 锚点")
        text = insert_before(text, "<!-- wf:progress:end -->", row)

        bid = None
        if state == "阻塞":
            ids = re.findall(r"\|\s*(B-\d+)\s*\|", text)
            bid = (
                f"B-{(max([int(x.split('-')[1]) for x in ids]) + 1) if ids else 1:03d}"
            )
            brow = (
                f"| {bid} | {args.blocker.strip()} | {args.ws} | "
                f"{args.action.strip()} | {now_str()} | 开放 |\n"
            )
            text = insert_before(text, "<!-- wf:blockers:end -->", brow)
        st.write_text(text, encoding="utf-8")
        write_header_field(st, "updated", today())

        msg = f"wf({args.run_id}): r{read_header(st).get('round', '?')} {args.ws} {args.action.strip()[:40]}"
        if args.commit:
            also = [_normalize_also_arg(p) for p in args.also]
            ok, info = git_commit([st] + also, msg)
            if ok:
                print(f"[OK] 已追加 + 已提交: {msg}")
            else:
                print(f"[WARN] 进度已写入，但 git commit 失败：{info}")
                print("       可修好 git 后手工提交；或用 --no-commit 静默跳过。")
        else:
            print("[OK] 已追加（--no-commit，未提交）")
        if bid:
            print(f"[BLOCKER] {bid} 已登记；回执里报这个 ID。")
    finally:
        lp = lock_path(rd)
        meta = read_lock(rd) or {}
        if lp.exists() and meta.get("agent") == args.agent:
            shutil.rmtree(lp, ignore_errors=True)
        elif lp.exists():
            print(
                f"[WARN] 锁已被 {meta.get('agent')} 接管，未强删他人锁", file=sys.stderr
            )


# ------------------------------------------------------------------ status shards
def _shard_dir(rd):
    return rd / "status-shards"


def _safe_agent(agent):
    return re.sub(r"[^0-9A-Za-z._-]+", "-", agent.strip()) or "agent"


def cmd_append_shard(args):
    rd = run_dir(args.run_id)
    if not args.action.strip() or not args.evidence.strip():
        die("--action/--evidence 不能为空")
    if args.state not in ("进行中", "完成", "阻塞"):
        die("--state 只允许 进行中 / 完成 / 阻塞")
    if args.state == "阻塞" and not args.blocker.strip():
        die("--state 阻塞 必须给 --blocker")
    d = _shard_dir(rd)
    d.mkdir(exist_ok=True)
    row = {
        "ts": now_str(),
        "agent": args.agent,
        "ws": args.ws,
        "action": args.action.strip(),
        "evidence": args.evidence.strip(),
        "state": args.state,
        "blocker": args.blocker.strip(),
    }
    path = d / f"{_safe_agent(args.agent)}.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"[OK] shard 已追加: {path.relative_to(ROOT)}")


def cmd_merge_shards(args):
    rd = run_dir(args.run_id)
    shard_dir = _shard_dir(rd)
    shard_files = sorted(shard_dir.glob("*.jsonl")) if shard_dir.is_dir() else []
    if not shard_files:
        print("(没有待合并的 status shard)")
        return
    agent = args.agent or "merge-shards"
    if not acquire_lock(rd, agent, wait=args.wait, steal=args.steal):
        die("拿不到 STATUS 锁，稍后重试", code=4)
    try:
        st = latest_status(rd)
        text = st.read_text(encoding="utf-8")
        if "<!-- wf:progress:end -->" not in text:
            die("STATUS 缺少 <!-- wf:progress:end --> 锚点")
        rows = []
        for sf in shard_files:
            for line in sf.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rows.append(json.loads(line))
        rows.sort(key=lambda r: str(r.get("ts", "")))
        added = 0
        for row in rows:
            ws = str(row.get("ws") or "")
            if not re.fullmatch(r"WS-\d+", ws):
                die(f"shard WS 格式非法: {ws!r}")
            prow = (
                f"| {row.get('ts', now_str())} | {row.get('agent', '-')} | {ws} | "
                f"{row.get('action', '')} | {row.get('evidence', '')} | {row.get('state', '完成')} |\n"
            )
            text = insert_before(text, "<!-- wf:progress:end -->", prow)
            if row.get("state") == "阻塞":
                ids = re.findall(r"\|\s*(B-\d+)\s*\|", text)
                bid = f"B-{(max([int(x.split('-')[1]) for x in ids]) + 1) if ids else 1:03d}"
                brow = (
                    f"| {bid} | {row.get('blocker')} | {ws} | {row.get('action', '')} | "
                    f"{row.get('ts', now_str())} | 开放 |\n"
                )
                text = insert_before(text, "<!-- wf:blockers:end -->", brow)
            added += 1
        st.write_text(text, encoding="utf-8")
        write_header_field(st, "state", "tdo-in-progress")
        write_header_field(st, "updated", today())
        archive = shard_dir / "merged" / datetime.now().strftime("%Y%m%d-%H%M%S")
        archive.mkdir(parents=True, exist_ok=True)
        for sf in shard_files:
            shutil.move(str(sf), str(archive / sf.name))
        print(f"[OK] 合并 {added} 条 shard 到 {st.name}；原 shard 归档 {archive.relative_to(ROOT)}")
    finally:
        lp = lock_path(rd)
        meta = read_lock(rd) or {}
        if lp.exists() and meta.get("agent") == agent:
            shutil.rmtree(lp, ignore_errors=True)
        elif lp.exists():
            print(f"[WARN] 锁已被 {meta.get('agent')} 接管，未强删他人锁", file=sys.stderr)


# ------------------------------------------------------------------ brief
def brief_text(role, run_id, name="", ws=""):
    rd = run_dir(run_id)
    h = read_header(rd / "PROJECT.md")
    n = h.get("round", "?")
    rel = f"runs/{run_id}"
    spec_line = (
        f"先读：{rel}/SPEC.md（本 run 特化规则，优先于通用手册）\n"
        if (rd / "SPEC.md").exists()
        else ""
    )
    safety_line = ""
    if (rd / "safety" / "config.json").exists():
        safety_line = (
            "本 run 已启用 H 盘安全门控：任何 H 盘状态变化只能经 "
            "`python3 scripts/hdrive_gate.py run`；不得直接 mv/cp/rm/robocopy。\n"
        )
    if role == "pmo":
        return f"""你是本工作流的 PMO。工作目录：{REPO}/{ROOT.name}
{spec_line}先读：roles/common-contract.md → roles/PMO.md → WORKFLOW.md §2/§4/§6
run：{rel}（第 {n} 轮；当前 PROJECT state={h.get("state", "?")}）
只写：{rel}/PROJECT.md
禁止：写 STATUS、新增 ISSUES 行、执行技术任务、替主会话拍板
台账例外：若 DECISIONS.md 有明确授权（如 D-008/D-012），可在收轮时按证据更新 ISSUES.xlsx 既有行的「状态」「关联决策ID」列，不改其他列
本轮要求：若 state=pmo-plan → 完成 §1–§5 计划与 §6 摘要，然后运行 `python3 scripts/wf.py state {run_id} PROJECT plan-ready --by pmo`；
          若 state=plan-ready（收轮）→ 读当轮 STATUS 与 ISSUES，更新 §3/§4/§5 与 §6 上报区，然后运行 `python3 scripts/wf.py state {run_id} PROJECT waiting-main --by pmo`
完成后按 WORKFLOW.md §3.2 回执（≤8 行），不要贴正文。"""
    if role == "tdo":
        agent = name or "tdo-a1"
        scope = (
            f"你负责：{ws}（以 PROJECT §4 该行为准；并发下不要碰其它 WS 的文件）"
            if ws
            else "你负责：<在 PROJECT §4 认领你的 WS，产出物/验收判据以该行为准>"
        )
        return f"""你是本工作流的 TDO（执行智能体）。工作目录：{REPO}/{ROOT.name}
{spec_line}{safety_line}先读：roles/common-contract.md → roles/TDO.md → WORKFLOW.md §5
run：{rel}（第 {n} 轮）
你的名字：{agent}；{scope}
写：你的产出物 + {rel}/STATUS-Round-{n}.md（必须用 wf.py 加锁追加；一条一提交）
命令：python3 scripts/wf.py append-status {run_id} --agent {agent} --ws WS-x --action "..." --evidence "..." [--also 产出物路径]
全部完成后：填写 STATUS 的「交接给 QA」区（完成定义对照 / 自检命令与结果 / 已知薄弱点），并追加最后一条进度。
禁止：改 PROJECT/ISSUES/DECISIONS；改别人的产出物；替主会话拍板；写 KB 正式域；绕过安全门控
完成后按 WORKFLOW.md §3.2 回执（≤8 行），不要贴日志。"""
    if role == "safety":
        reviewer = name or "safety-a1"
        return f"""你是本 run 的 SAFETY（独立安全审核员）。工作目录：{REPO}/{ROOT.name}
{spec_line}先读：roles/common-contract.md → roles/SAFETY.md → WORKFLOW.md §6
run：{rel}（第 {n} 轮）
你的名字：{reviewer}
只写：{rel}/safety/reviews/ACT-*.json（只能通过 hdrive_gate.py review 命令）
输入：{rel}/safety/config.json、actions/、gates/ 与 dry-run/清单证据
硬要求：只处理 gate.status=FAIL 的 action；一次只审一个 action；核对 digest；不得自审、不得批量、不得执行
你可以 approve 或 reject；red 动作 approve 后仍需独立人工 human-approve。未通过/未审核的 action 一律不得执行。
禁止：提出/修改 action；修改 gate 结果；直接写 H 盘；写 STATUS/PROJECT/ISSUES/DECISIONS；绕过 hdrive_gate.py
完成后按 roles/SAFETY.md §七 回执（≤8 行），并给出 pending/approve/reject 数字。"""
    return f"""你是本工作流的 QA（独立核查）。工作目录：{REPO}/{ROOT.name}
{spec_line}{safety_line}先读：roles/common-contract.md → roles/QA.md → WORKFLOW.md §6
run：{rel}（第 {n} 轮）
只写：{rel}/ISSUES.xlsx（用 scripts/issues.py，ID 自动分配）
输入：当轮 STATUS、PROJECT §1/§3/§4、产出物、上轮未关闭 ISSUES
要求：按 QA.md §2 清单逐条核查；S1 必须标“需主会话决策=是”；只报不改
若启用安全门控：必须核对 safety/actions、gates、reviews、human-approvals、executions 的完整性与摘要一致性，任何未授权执行记 S1。
完成后：运行 `python3 scripts/wf.py state {run_id} STATUS qa-done --by qa`，并按 §3.2 回执（≤8 行）。"""


def cmd_brief(args):
    print(f"===== {args.role.upper()}-BRIEF（复制以下内容给 opencode 会话）=====")
    print(brief_text(args.role, args.run, args.agent))


# ------------------------------------------------------------------ opencode 直连
SERVER_STATE = ROOT / ".opencode-server.json"
SERVER_LOG = ROOT / ".opencode-server.log"
OC_PROVIDER = "opencode-go"
OC_MODEL = "deepseek-v4.1-flash"
OC_AGENT = "minimal"
DELEGATE_BACKENDS = ("auto", "v1-http", "v2-cli", "dsh")
# v1 HTTP API 只存在于 opencode 1.x；2.x 已移除（POST /session -> 405）。
# 需要并存旧版时用 OPENCODE_BIN 指向兼容二进制。
OC_BIN = os.environ.get("OPENCODE_BIN", "opencode")


def _oc_cli_version(binary=None):
    """探测 opencode CLI 版本，返回 (major, raw|reason)。

    只读探测：`--version` 不需要网络或常驻服务；失败返回 (None, 原因)。
    """
    binary = binary or OC_BIN
    try:
        proc = subprocess.run(
            [binary, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        return None, f"未找到可执行文件 {binary}"
    except Exception as e:  # noqa: BLE001  超时/权限/执行失败
        return None, f"无法执行 {binary} --version: {e}"
    raw = (proc.stdout or proc.stderr or "").strip()
    if proc.returncode != 0:
        return None, f"{binary} --version 退出码 {proc.returncode}: {raw[:200]}"
    m = re.search(r"(?i)\bv?(\d+)\.(\d+)(?:\.\d+)?", raw)
    if not m:
        return None, f"无法识别版本输出: {raw[:200]!r}"
    return int(m.group(1)), (raw.splitlines()[0] if raw else "")


def require_v1_http(context, binary=None):
    """走 v1 HTTP API 前快速失败：opencode 2.x 已删除该端点（405）。

    只在 `serve_start` 调用（唯一起点）；`delegate`/`squad` 默认经
    `_resolve_base` 自动拉起服务，因此同一守卫会先于 HTTP 生效。
    `--dry-run` 不经过这里，仍可离线预览 BRIEF。
    """
    major, detail = _oc_cli_version(binary)
    hint = (
        "改用 `opencode run`（v2 CLI 原生；本仓未内置 v2 adapter，插件线有 opencode_delegate.py 外部封装），"
        "或用 OPENCODE_BIN=/path/to/opencode-1.x 指定兼容二进制"
    )
    if major == 1:
        return
    if major is None:
        die(f"opencode 版本守卫失败（{context}）：{detail}；{hint}")
    die(f"当前 opencode 版本 {detail} 不支持 v1 HTTP API（{context}）；{hint}")


def _auth_header():
    pw = os.environ.get("OPENCODE_SERVER_PASSWORD")
    if not pw:
        return {}
    import base64

    token = base64.b64encode(f"opencode:{pw}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def api(base, method, path, body=None, timeout=120):
    import urllib.error
    import urllib.request

    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        base.rstrip("/") + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", **_auth_header()},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:400]
        die(f"opencode API {method} {path} 失败: HTTP {e.code} {detail}")
    except Exception as e:
        die(f"opencode API {method} {path} 失败: {e}")
    return json.loads(raw) if raw.strip() else {}


def server_up(url, timeout=3):
    import urllib.request

    try:
        req = urllib.request.Request(
            url.rstrip("/") + "/api/health", headers=_auth_header()
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def load_server_state():
    if SERVER_STATE.exists():
        try:
            return json.loads(SERVER_STATE.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def serve_start(port=0, directory=None, wait=30, pure=True):
    require_v1_http("serve start")
    st = load_server_state()
    if st and server_up(st.get("url", "")):
        return st
    cwd = Path(directory) if directory else ROOT
    if not cwd.is_dir():
        die(f"目录不存在: {cwd}")
    SERVER_LOG.write_text("", encoding="utf-8")
    # 必须使用与版本探测相同的二进制，否则 OPENCODE_BIN 只影响探测、不影响实际 launch。
    cmd = [OC_BIN, "serve", "--port", str(port), "--hostname", "127.0.0.1"]
    if pure:
        cmd.append("--pure")  # 禁外部插件：冷启动快、系统 prompt 小
    with open(SERVER_LOG, "ab") as fh:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            stdout=fh,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    pat = re.compile(r"listening on (http://127\.0\.0\.1:\d+)")
    url, deadline = None, time.time() + wait
    while time.time() < deadline:
        m = pat.search(SERVER_LOG.read_text(encoding="utf-8", errors="replace"))
        if m:
            url = m.group(1)
            break
        if proc.poll() is not None:
            die(
                f"opencode serve 退出（code={proc.returncode}）："
                f"{SERVER_LOG.read_text(encoding='utf-8', errors='replace')[-300:]}"
            )
        time.sleep(0.5)
    if not url:
        die(f"opencode serve {wait}s 内未就绪，见 {SERVER_LOG}")
    state = {
        "url": url,
        "pid": proc.pid,
        "dir": str(cwd),
        "started_at": now_str(),
        "pure": bool(pure),
    }
    SERVER_STATE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # 预热：第一次建 session 会加载配置/工具（非 pure 时约 30s），先付掉
    t0 = time.time()
    try:
        wu = api(
            url,
            "POST",
            "/session",
            {
                "title": "wf-warmup (可删)",
                "model": {"id": OC_MODEL, "providerID": OC_PROVIDER},
            },
            timeout=180,
        )
        wid = wu.get("id") or (wu.get("data") or {}).get("id")
        if wid:
            try:
                api(url, "DELETE", f"/session/{wid}", timeout=30)
            except SystemExit:
                pass
        print(
            f"[OK] opencode serve 已启动: {url}（cwd={cwd}，pid={proc.pid}，"
            f"pure={pure}，预热 {time.time() - t0:.1f}s）"
        )
    except SystemExit:
        print(f"[WARN] 服务已起但预热失败（首个 delegate 可能变慢）: {url}")
    return state


def serve_stop():
    st = load_server_state()
    if not st:
        print("(无记录的服务)")
        return
    pid = st.get("pid")
    if pid:
        try:
            os.kill(int(pid), 15)
        except ProcessLookupError:
            pass
        except Exception as e:
            print(f"[WARN] kill {pid} 失败: {e}")
        time.sleep(1)
        try:
            os.kill(int(pid), 0)
            os.kill(int(pid), 9)
        except ProcessLookupError:
            pass
    try:
        SERVER_STATE.unlink()
    except FileNotFoundError:
        pass
    print(f"[OK] 已停止 {st.get('url')}")


def cmd_serve(args):
    if args.action == "start":
        serve_start(args.port, args.dir or None, pure=not args.impure)
    elif args.action == "stop":
        serve_stop()
    else:
        st = load_server_state()
        if not st:
            print("(未启动；delegate 会自动拉起)")
            return
        up = server_up(st.get("url", ""))
        print(
            f"{'运行中' if up else '已停止'}  {st.get('url')}  "
            f"cwd={st.get('dir')}  pid={st.get('pid')}  启动于 {st.get('started_at')}"
        )


DELEGATION_LOCK = threading.Lock()


def _delegate_guards(rd, role, force=False):
    ph = read_header(rd / "PROJECT.md")
    st_file = latest_status(rd, required=False)
    sh = read_header(st_file) if st_file else {}
    if not force:
        if role == "pmo" and ph.get("state") not in ("pmo-plan", "plan-ready"):
            die(
                f"PMO 委派要求 PROJECT.state=pmo-plan|plan-ready，当前 {ph.get('state')}"
            )
        if role == "tdo" and ph.get("state") != "plan-ready":
            die(f"TDO 委派要求 PROJECT.state=plan-ready，当前 {ph.get('state')}")
        if role == "tdo" and sh.get("state") not in ("tdo-pending", "tdo-in-progress"):
            die(
                f"TDO 委派要求 STATUS.state=tdo-pending|tdo-in-progress，当前 {sh.get('state')}"
            )
        if role == "qa" and sh.get("state") != "qa-pending":
            die(f"QA 委派要求 STATUS.state=qa-pending，当前 {sh.get('state')}")
        if role == "safety":
            if not (rd / "safety" / "config.json").exists():
                die("SAFETY 委派要求本 run 已启用 safety/config.json 安全门控")
            if ph.get("state") != "plan-ready":
                die(f"SAFETY 委派要求 PROJECT.state=plan-ready，当前 {ph.get('state')}")
            if sh.get("state") not in ("tdo-in-progress",):
                die(
                    "SAFETY 委派要求 STATUS.state=tdo-in-progress（TDO 已开始提出 action），"
                    f"当前 {sh.get('state')}"
                )
    return ph, sh


def _resolve_base(server, port):
    if server:
        if not server_up(server):
            die(f"指定服务不可用: {server}")
        return server
    return serve_start(port).get("url")


def _resolve_delegate_backend(requested="auto"):
    """Resolve the delegation backend without starting a server.

    auto: opencode 2.x -> v2-cli; opencode 1.x -> v1-http; no opencode but dsh
    present -> dsh. Explicit values are returned unchanged for the caller to
    validate/fail at execution time.
    """
    if requested not in DELEGATE_BACKENDS:
        die(f"--backend 必须是 {' / '.join(DELEGATE_BACKENDS)}，收到 {requested!r}")
    if requested != "auto":
        return requested
    major, detail = _oc_cli_version()
    if major == 2:
        return "v2-cli"
    if major == 1:
        return "v1-http"
    if shutil.which("dsh"):
        return "dsh"
    die(
        "auto backend 无法选择："
        f"opencode 探测={detail}; dsh 不在 PATH。"
        "请显式指定 --backend v2-cli|dsh，或安装对应 CLI。"
    )


def _api_with_heartbeat(base, sid, body, timeout, heartbeat=60, tag=""):
    """后台线程发 message，主线程每 heartbeat 秒打印一行心跳（S-2）。

    长委派实测可跑数十分钟（见 burn-postmortem F3）；此前仅在返回时记账，
    期间无任何输出、无法区分"在跑"与"卡死"。失败（含 api() 的 die）在主线程抛回。
    """
    interval = (
        heartbeat if isinstance(heartbeat, (int, float)) and heartbeat > 0 else 60
    )
    box = {}
    t0 = time.time()

    def _do():
        try:
            box["resp"] = api(
                base, "POST", f"/session/{sid}/message", body, timeout=timeout
            )
        except BaseException as e:  # noqa: BLE001  含 die() 抛出的 SystemExit
            box["err"] = e

    th = threading.Thread(target=_do, daemon=True)
    th.start()
    while th.is_alive():
        th.join(timeout=interval)
        if th.is_alive():
            print(
                f"[HEARTBEAT] {tag}session={sid} 已等待 {int(time.time() - t0)}s",
                flush=True,
            )
    if "err" in box:
        err = box["err"]
        if isinstance(err, SystemExit):
            raise err
        die(f"opencode API POST /session/{sid}/message 失败: {err}")
    return box["resp"]


def run_one_delegation(
    run_id, role, name, ws, model, oc_agent, base, timeout, heartbeat=60
):
    """建 session → 发 BRIEF → 同步收回执。返回结果字典；失败抛异常。"""
    rd = run_dir(run_id)
    if "/" not in model:
        raise RuntimeError("--model 格式应为 providerID/modelID")
    provider, model_id = model.split("/", 1)
    brief = brief_text(role, run_id, name, ws)
    ph = read_header(rd / "PROJECT.md")
    title = f"wf {run_id} r{ph.get('round', '?')} {role} {name}"
    s = api(
        base,
        "POST",
        "/session",
        {"title": title, "model": {"id": model_id, "providerID": provider}},
        timeout=180,
    )
    sid = s.get("id") or (s.get("data") or {}).get("id")
    if not sid:
        raise RuntimeError(f"建 session 失败: {s}")
    t0 = time.time()
    resp = _api_with_heartbeat(
        base,
        sid,
        {
            "model": {"providerID": provider, "modelID": model_id},
            "agent": oc_agent,
            "parts": [{"type": "text", "text": brief}],
        },
        timeout,
        heartbeat=heartbeat,
        tag=f"{role}/{name} ",
    )
    dt = time.time() - t0
    info = resp.get("info", {}) or {}
    text = "\n".join(
        p.get("text", "") for p in (resp.get("parts") or []) if p.get("type") == "text"
    ).strip()
    return {
        "name": name,
        "ws": ws,
        "sid": sid,
        "text": text,
        "cost": info.get("cost"),
        "tokens": info.get("tokens") or {},
        "dt": dt,
        "model": model,
        "oc_agent": oc_agent,
    }


def system_free_mb():
    """Best-effort free memory in MiB; None if the platform cannot report it."""
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) // 1024
    except OSError:
        pass
    try:
        import psutil

        return int(psutil.virtual_memory().available // (1024 * 1024))
    except Exception:
        return None


def resource_admission(agent_count, force=False):
    """Bounded local admission; returns a dict or exits with QUEUED_BY_RESOURCE."""
    max_agents = int(os.environ.get("WF_MAX_CONCURRENT_AGENTS", "6"))
    min_free_mb = int(os.environ.get("WF_MIN_FREE_MEM_MB", "512"))
    free = system_free_mb()
    result = {
        "agentsRequested": int(agent_count),
        "agentsMax": max_agents,
        "freeMemMb": free,
        "minFreeMemMb": min_free_mb,
        "admitted": True,
        "reason": "",
    }
    if force:
        result["reason"] = "forced"
        return result
    if agent_count > max_agents:
        result.update(admitted=False, reason="QUEUED_BY_RESOURCE: too many agents")
    elif free is not None and free < min_free_mb:
        result.update(admitted=False, reason="QUEUED_BY_RESOURCE: low free memory")
    if not result["admitted"]:
        print(result["reason"], file=sys.stderr)
        die(
            f"资源准入拒绝：agents={agent_count}/{max_agents}，free={free}MiB "
            f"(min={min_free_mb}MiB)。增加资源或显式加 --skip-resource-check/--force。",
            code=4,
        )
    return result


def cmd_resource_check(args):
    result = resource_admission(args.agents, force=args.force)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"admitted={result['admitted']} agents={result['agentsRequested']}/"
            f"{result['agentsMax']} free={result['freeMemMb']}MiB"
        )


def run_one_headless_delegation(
    run_id, role, name, ws, model, backend, timeout, heartbeat=60
):
    """Run one delegation through the canonical headless CLI adapter.

    Returns a result dict compatible with `_log_delegation`/`cmd_squad`.
    """
    if backend not in ("v2-cli", "dsh"):
        raise ValueError(f"not a headless backend: {backend}")
    brief = brief_text(role, run_id, name, ws)
    try:
        res = headless_adapter.run(
            backend,
            brief,
            model=model,
            timeout=timeout,
            cwd=ROOT,
            heartbeat=heartbeat,
        )
    except FileNotFoundError as e:
        raise RuntimeError(f"{backend} 可执行文件不存在: {e}") from e
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"{backend} 委派执行失败: {e}") from e
    res.update(
        {
            "name": name,
            "ws": ws,
            "oc_agent": "",
            "backend": backend,
            "brief": brief,
        }
    )
    return res


def _log_delegation(run_id, role, name, ws, res):
    rd = run_dir(run_id)
    ph = read_header(rd / "PROJECT.md")
    tok = res.get("tokens") or {}
    cache = tok.get("cache") or {}
    ts = now_str()
    rdir = rd / "delegations"
    rdir.mkdir(exist_ok=True)
    slug = re.sub(r"[^0-9A-Za-z._-]+", "-", f"{ts}-{role}-{name}")
    receipt = rdir / f"{slug}.md"
    receipt.write_text(
        f"# 委派回执 · {role.upper()} · {name}" + (f" · {ws}" if ws else "") + "\n\n"
        f"- 时间：{ts} ｜ 轮次：{ph.get('round', '?')} ｜ session：`{res.get('sid')}`\n"
        f"- 后端：{res.get('backend', 'v1-http')} ｜ 模型：{res.get('model')} ｜ "
        f"opencode agent：{res.get('oc_agent') or '-'}\n"
        f"- 耗时：{res.get('dt', 0):.1f}s ｜ cost：{res.get('cost')} ｜ "
        f"tokens：{json.dumps(tok, ensure_ascii=False)}\n\n"
        "## 原始回执\n\n" + (res.get("text") or "(空)") + "\n",
        encoding="utf-8",
    )
    text = res.get("text") or ""
    summary = re.sub(r"\s+", " ", (text.splitlines()[0] if text else "(空)"))[:60]
    with DELEGATION_LOCK:
        log_md = rd / "DELEGATIONS.md"
        if not log_md.exists():
            log_md.write_text(
                f"# DELEGATIONS — {run_id}\n\n"
                "> 主会话自动委派记录（`wf.py delegate` / `wf.py squad`）｜只增不改｜回执正文见 `delegations/`\n\n"
                "| 时间 | 轮次 | 角色 | 执行体 | WS | session | 状态 | 耗时 | cost($) | tokens(in/out/cache-r) | 回执摘要 |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n",
                encoding="utf-8",
            )
        with open(log_md, "a", encoding="utf-8") as f:
            f.write(
                f"| {ts} | {ph.get('round', '?')} | {role} | {name} | {ws or '-'} | `{res.get('sid')}` | ok | "
                f"{res.get('dt', 0):.1f}s | {res.get('cost')} | "
                f"{tok.get('input')}/{tok.get('output')}/{cache.get('read')} | {summary} |\n"
            )
    return receipt


def _print_delegation_result(res, receipt):
    backend = res.get("backend", "v1-http")
    print(f"[OK] 委派完成（backend={backend}，{res['dt']:.1f}s，cost={res.get('cost')}）")
    print(f"   session: {res['sid']}")
    print(f"   回执归档: {receipt.relative_to(ROOT)}")
    print("--- 回执 ---")
    print(res.get("text") or "(空)")


def cmd_delegate(args):
    rd = run_dir(args.run_id)
    _delegate_guards(rd, args.role, args.force)
    name = args.name or {
        "pmo": "pmo",
        "tdo": "tdo-a1",
        "qa": "qa",
        "safety": "safety-a1",
    }[args.role]
    model = args.model or f"{OC_PROVIDER}/{OC_MODEL}"
    if "/" not in model:
        die("--model 格式应为 providerID/modelID，如 opencode-go/deepseek-v4.1-flash")
    backend = _resolve_delegate_backend(getattr(args, "backend", "auto"))
    if args.dry_run:
        print(
            f"[DRY-RUN] role={args.role} name={name} ws={args.ws or '-'} "
            f"model={model} backend={backend} oc-agent={args.oc_agent}"
        )
        if backend in ("v2-cli", "dsh"):
            cmd, _stdin = headless_adapter.build_command(
                backend, "<BRIEF>", model=model
            )
            print("[DRY-RUN] command:", " ".join(cmd))
        print(brief_text(args.role, args.run_id, name, args.ws))
        return
    if backend == "v1-http":
        base = _resolve_base(args.server, args.port)
        res = run_one_delegation(
            args.run_id,
            args.role,
            name,
            args.ws,
            model,
            args.oc_agent,
            base,
            args.timeout,
            args.heartbeat,
        )
    else:
        res = run_one_headless_delegation(
            args.run_id,
            args.role,
            name,
            args.ws,
            model,
            backend,
            args.timeout,
            args.heartbeat,
        )
    receipt = _log_delegation(args.run_id, args.role, name, args.ws, res)
    _print_delegation_result(res, receipt)
    if res.get("timed_out") or res.get("exit_code") not in (0, None):
        print(
            f"[ERROR] {backend} 委派失败 exit={res.get('exit_code')} "
            f"stderr={res.get('stderr_tail', '')[:300]}",
            file=sys.stderr,
        )
        raise SystemExit(res.get("exit_code") or 1)


def cmd_squad(args):
    """并行扇出：一条命令把 N 个 TDO 同时发出去（各自 WS，互不重叠）。"""
    rd = run_dir(args.run_id)
    if args.role != "tdo":
        die("squad 目前只支持 --role tdo（PMO/QA 各只有 1 个）")
    _delegate_guards(rd, "tdo", args.force)
    agents = []
    for item in args.agents.split(","):
        item = item.strip()
        if not item:
            continue
        if ":" in item:
            n, w = item.split(":", 1)
        else:
            n, w = item, ""
        agents.append((n.strip(), w.strip()))
    if len(agents) < 2:
        die("至少 2 个执行体，格式 --agents 'tdo-a1:WS-1,tdo-a2:WS-2'")
    if not all(w for _, w in agents):
        die("squad 里每个执行体都必须带 WS（并发下不允许抢同一片）")
    names = [n for n, _ in agents]
    if len(set(names)) != len(names):
        die("执行体名字重复")
    if not getattr(args, "skip_resource_check", False):
        resource_admission(len(agents), force=getattr(args, "force", False))
    model = args.model or f"{OC_PROVIDER}/{OC_MODEL}"
    if "/" not in model:
        die("--model 格式应为 providerID/modelID")
    backend = _resolve_delegate_backend(getattr(args, "backend", "auto"))
    if args.dry_run:
        for n, w in agents:
            print(f"===== [DRY-RUN] {n} / {w} backend={backend} =====")
            if backend in ("v2-cli", "dsh"):
                cmd, _stdin = headless_adapter.build_command(
                    backend, "<BRIEF>", model=model
                )
                print("[DRY-RUN] command:", " ".join(cmd))
            print(brief_text("tdo", args.run_id, n, w))
        return
    base = _resolve_base(args.server, args.port) if backend == "v1-http" else None
    print(
        f"[..] 扇出 {len(agents)} 个 TDO（backend={backend}，jobs≤{args.jobs}，"
        f"timeout={args.timeout}s）"
    )
    results, errors = [], []

    def _submit_one(ex, n, w):
        if backend == "v1-http":
            return ex.submit(
                run_one_delegation,
                args.run_id,
                "tdo",
                n,
                w,
                model,
                args.oc_agent,
                base,
                args.timeout,
                args.heartbeat,
            )
        return ex.submit(
            run_one_headless_delegation,
            args.run_id,
            "tdo",
            n,
            w,
            model,
            backend,
            args.timeout,
            args.heartbeat,
        )

    with ThreadPoolExecutor(max_workers=max(1, min(args.jobs, len(agents)))) as ex:
        futs = {_submit_one(ex, n, w): (n, w) for n, w in agents}
        for fut in as_completed(futs):
            n, w = futs[fut]
            try:
                res = fut.result()
                receipt = _log_delegation(args.run_id, "tdo", n, w, res)
                results.append(res)
                print(
                    f"[OK]   {n:<10} {w:<8} {res['dt']:7.1f}s  "
                    f"cost={res.get('cost')}  ({receipt.name})"
                )
                if res.get("timed_out") or res.get("exit_code") not in (0, None):
                    errors.append(
                        (n, f"exit={res.get('exit_code')} {res.get('stderr_tail', '')[:120]}")
                    )
            except BaseException as e:  # noqa: BLE001
                errors.append((n, str(e)))
                print(f"[FAIL] {n:<10} {w:<8} {e}", file=sys.stderr)
    total_cost = sum(float(r.get("cost") or 0) for r in results)
    total_tok = sum((r.get("tokens") or {}).get("input") or 0 for r in results)
    print(
        f"== squad 汇总: 成功 {len(results)}/{len(agents)}，"
        f"¥cost={total_cost:.6f}，input_tokens={total_tok} =="
    )
    if errors:
        sys.exit(1)


def cmd_ledger(args):
    """汇总 DELEGATIONS.md：按角色统计次数/成本/tokens/耗时。"""
    log_md = run_dir(args.run_id) / "DELEGATIONS.md"
    if not log_md.exists():
        print("(还没有委派记录)")
        return
    lines = log_md.read_text(encoding="utf-8").splitlines()
    header = None
    for line in lines:
        if line.startswith("|") and "时间" in line and "角色" in line:
            header = [x.strip() for x in line.strip().strip("|").split("|")]
            break
    rows = []
    for line in lines:
        if not line.startswith("|") or "---" in line or "时间" in line:
            continue
        f = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(f) < 9:
            continue
        rows.append(f)

    def col(f, name, fallback):
        if header and name in header:
            i = header.index(name)
            return f[i] if i < len(f) else fallback
        return fallback

    def num(x):
        try:
            return float(str(x).replace("s", ""))
        except (TypeError, ValueError):
            return 0.0

    def tok3(x):
        parts = [p or "0" for p in str(x).split("/")][:3]
        while len(parts) < 3:
            parts.append("0")
        try:
            return [int(p) for p in parts]
        except ValueError:
            return [0, 0, 0]

    by_role = {}
    for f in rows:
        role = col(f, "角色", f[2])
        cost = num(col(f, "cost($)", f[7] if len(f) == 10 else f[8]))
        ti, to, tc = tok3(
            col(f, "tokens(in/out/cache-r)", f[8] if len(f) == 10 else f[9])
        )
        dt = num(col(f, "耗时", f[6] if len(f) == 10 else f[7]))
        d = by_role.setdefault(
            role, {"n": 0, "cost": 0.0, "dt": 0.0, "in": 0, "out": 0, "cache": 0}
        )
        d["n"] += 1
        d["cost"] += cost
        d["dt"] += dt
        d["in"] += ti
        d["out"] += to
        d["cache"] += tc
    tot = {
        k: sum(v[k] for v in by_role.values())
        for k in ("n", "cost", "dt", "in", "out", "cache")
    }
    print(f"== 委派账本 · {args.run_id} ==")
    print(
        f"{'角色':<6}{'次数':>4}{'cost($)':>12}{'耗时(s)':>10}{'input':>10}{'output':>8}{'cache-r':>10}"
    )
    for role, d in sorted(by_role.items()):
        print(
            f"{role:<6}{d['n']:>4}{d['cost']:>12.6f}{d['dt']:>10.0f}{d['in']:>10}{d['out']:>8}{d['cache']:>10}"
        )
    print("-" * 62)
    print(
        f"{'合计':<6}{tot['n']:>4}{tot['cost']:>12.6f}{tot['dt']:>10.0f}{tot['in']:>10}{tot['out']:>8}{tot['cache']:>10}"
    )
    if tot["n"]:
        print(f"平均单次 {tot['dt'] / tot['n']:.0f}s（并行时按最长者近似墙钟）")


def cmd_commit_run(args):
    """Round-end commit for one run directory (no core/source files)."""
    rd = run_dir(args.run_id)
    paths = [rd]
    for raw in getattr(args, "also", []) or []:
        p = _normalize_also_arg(raw)
        try:
            p.relative_to(rd.resolve())
        except ValueError:
            die(f"--also 必须位于 {rd} 内: {p}")
        paths.append(p)
    msg = f"wf({args.run_id}): {args.message or 'round-end commit'}"
    if args.dry_run:
        print("[DRY-RUN] git add --")
        for p in paths:
            print(" ", p)
        return
    ok, info = git_commit(paths, msg)
    if not ok:
        die(f"run-end commit 失败: {info}")
    print(f"[OK] {msg}")
    print(info.splitlines()[0] if info else "")


def cmd_commit(args):
    """真实项目仓的保守提交：只 add 指定 pathspec，不 push。"""
    repo = Path(args.repo).expanduser().resolve()
    if not (repo / ".git").exists():
        die(f"不是 git 仓库: {repo}")
    if not args.paths:
        die(
            "用法: wf.py commit --repo <项目仓> --run <id> --round N --message '...' -- <path> [path...]"
        )
    r = subprocess.run(
        ["git", "-C", str(repo), "add", "--"] + args.paths,
        capture_output=True,
        text=True,
    )
    if r.returncode:
        die(f"git add 失败: {r.stdout}{r.stderr}")
    d = subprocess.run(
        ["git", "-C", str(repo), "diff", "--cached", "--stat"],
        capture_output=True,
        text=True,
    )
    if not d.stdout.strip():
        die("没有暂存到任何变更（路径是否写对？）")
    msg = f"audit({args.run}) r{args.round}: {args.message}"
    c = subprocess.run(
        ["git", "-C", str(repo), "commit", "-m", msg], capture_output=True, text=True
    )
    if c.returncode:
        die(f"git commit 失败: {c.stdout}{c.stderr}")
    print(d.stdout.strip())
    head = subprocess.run(
        ["git", "-C", str(repo), "log", "-1", "--oneline"],
        capture_output=True,
        text=True,
    ).stdout.strip()
    print(f"[OK] 已提交: {head}")
    print("[提示] 未 push（按约定 push 由人确认；opencode 权限里 push=ask）")


# ------------------------------------------------------------------ evidence pack
def _cmd_version(cmd):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        raw = (p.stdout or p.stderr or "").strip().splitlines()
        return raw[0] if raw else f"rc={p.returncode}"
    except Exception as exc:  # noqa: BLE001
        return f"unavailable: {exc}"


def cmd_evidence_pack(args):
    rd = run_dir(args.run_id)
    out = Path(args.out) if args.out else rd / "reports" / "evidence-pack.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    status = subprocess.run(
        ["git", "-C", str(REPO), "status", "--short"], capture_output=True, text=True
    )
    head = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True
    )
    files = []
    for p in sorted(rd.rglob("*")):
        if not p.is_file() or p == out or p.name.endswith((".pyc", ".sqlite")):
            continue
        try:
            import hashlib

            h = hashlib.sha256(p.read_bytes()).hexdigest()
            files.append((str(p.relative_to(rd)), p.stat().st_size, h))
        except OSError:
            continue
    pytest_line = "not requested"
    if args.pytest:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=args.test_timeout,
        )
        tail = [ln for ln in (proc.stdout or proc.stderr or "").splitlines() if ln.strip()]
        pytest_line = f"rc={proc.returncode}; " + (tail[-1] if tail else "(no summary)")
    lines = [
        f"# EVIDENCE PACK — {args.run_id}",
        "",
        f"- generatedAt: `{datetime.now().astimezone().isoformat(timespec='seconds')}`",
        f"- gitHead: `{(head.stdout or '').strip() or head.stderr.strip()}`",
        f"- workspace: `{ROOT}`",
        f"- python: `{sys.version.split()[0]}`",
        f"- node: `{_cmd_version(['node', '--version'])}`",
        f"- opencode: `{_cmd_version([os.environ.get('OPENCODE_BIN', 'opencode'), '--version'])}`",
        f"- dsh: `{_cmd_version([os.environ.get('DSH_BIN', 'dsh'), '--version'])}`",
        f"- rig: `{_cmd_version(['rig', '--version'])}`",
        f"- pytest: `{pytest_line}`",
        "",
        "## Git status",
        "",
        "```text",
        (status.stdout or "").rstrip() or "(clean)",
        "```",
        "",
        "## Run file hashes",
        "",
        "| path | bytes | sha256 |",
        "| --- | ---: | --- |",
    ]
    lines += [f"| `{rel}` | {size} | `{sha}` |" for rel, size, sha in files]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] evidence pack: {out}")
    if args.json:
        print(json.dumps({"out": str(out), "files": len(files), "pytest": pytest_line}, ensure_ascii=False))


# ------------------------------------------------------------------ status-all
def _scan_run_status(run_path: Path) -> dict:
    proj = read_header(run_path / "PROJECT.md")
    st_file = latest_status(run_path, required=False)
    status = read_header(st_file) if st_file else {}
    dec = read_header(run_path / "DECISIONS.md")
    lock = read_lock(run_path)
    issue_rows = []
    issue_error = ""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import issues as issues_mod

        xlsx = run_path / "ISSUES.xlsx"
        if xlsx.exists() or issues_mod.jsonl_path(xlsx).exists():
            issue_rows = issues_mod.read_rows(xlsx)
        else:
            issue_error = "missing ISSUES ledger"
    except SystemExit as exc:
        issue_error = f"ISSUES read blocked: {exc}"
    except Exception as exc:  # noqa: BLE001
        issue_error = str(exc)
    open_s1s2 = [
        r.get("ID")
        for r in issue_rows
        if r.get("严重度") in ("S1", "S2") and r.get("状态") not in ("已关闭", "挂起")
    ]
    bridge_schema = None
    bridge = run_path / "openrig" / "OPENRIG-BRIDGE.json"
    if bridge.is_file():
        try:
            bridge_schema = json.loads(bridge.read_text(encoding="utf-8")).get("schemaVersion")
        except Exception:
            bridge_schema = "unreadable"
    return {
        "run": run_path.name,
        "round": proj.get("round"),
        "projectState": proj.get("state"),
        "statusState": status.get("state"),
        "decisionsState": dec.get("state"),
        "baseline": proj.get("baseline"),
        "primaryType": proj.get("primary_type"),
        "maturity": proj.get("maturity"),
        "hasRoundPlan": (run_path / "ROUND-PLAN.md").is_file(),
        "lock": lock,
        "issueRows": len(issue_rows),
        "openS1S2": open_s1s2,
        "issueError": issue_error,
        "openrigBridgeSchema": bridge_schema,
    }


def cmd_status_all(args):
    rows = []
    for run_path in sorted(RUNS.iterdir(), key=lambda p: p.name):
        if not run_path.is_dir() or not (run_path / "PROJECT.md").is_file():
            continue
        try:
            rows.append(_scan_run_status(run_path))
        except SystemExit:
            raise
        except Exception as exc:  # noqa: BLE001
            rows.append({"run": run_path.name, "error": str(exc)})
    if args.json:
        print(json.dumps({"runs": rows, "count": len(rows)}, ensure_ascii=False, indent=2))
        return
    print(f"runs={len(rows)}")
    for row in rows:
        if row.get("error"):
            print(f"{row['run']}\tERROR\t{row['error']}")
            continue
        lock = "locked" if row.get("lock") else "-"
        open_s = ",".join(row.get("openS1S2") or []) or "-"
        print(
            f"{row['run']}\tr{row.get('round')}\t{row.get('projectState')}/"
            f"{row.get('statusState')}\t{lock}\topenS1S2={open_s}"
        )


# ------------------------------------------------------------------ doctor
PLAN_GATE_KEYS = ("contract", "produces", "gate", "budget", "NOT-DOING")
CONTRACT_TYPES = ("strategy", "research", "diff", "architecture", "optimize", "verify", "audit")


def _status_binding_checks(proj_text, status_text):
    """Check WS ownership/binding in STATUS progress and QA handoff sections."""
    errors, warns = [], []
    proj_ws = set()
    proj_section = section(proj_text, "## 4.", "## 5.")
    for line in proj_section.splitlines():
        if line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cells and re.fullmatch(r"WS-\d+", cells[0]):
                proj_ws.add(cells[0])
    progress = section(status_text, "<!-- wf:progress:start -->", "<!-- wf:progress:end -->")
    seen_agent_ws = {}
    for line in progress.splitlines():
        if not line.strip().startswith("|") or "---" in line or "时间" in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6:
            continue
        ts, agent, ws, action, evidence, state = cells[:6]
        if not agent or agent == "-":
            errors.append("STATUS 进度行缺执行体")
        if not re.fullmatch(r"WS-\d+", ws):
            errors.append(f"STATUS 进度行 WS 格式非法: {ws!r}")
        elif proj_ws and ws not in proj_ws:
            errors.append(f"STATUS 进度行 {ws} 未在 PROJECT §4 登记")
        if not action:
            errors.append("STATUS 进度行缺动作")
        if not evidence:
            errors.append("STATUS 进度行缺证据")
        if agent and ws:
            seen_agent_ws.setdefault(agent, set()).add(ws)
    for agent, ws_set in seen_agent_ws.items():
        if len(ws_set) > 1:
            warns.append(f"执行体 {agent} 本轮跨多个 WS: {', '.join(sorted(ws_set))}")
    hand = section(status_text, "## 交接给 QA", "<!-- wf:handoff:start -->")
    hand_ws = re.findall(r"\*\*(WS-\d+)", hand)
    dup = sorted({w for w in hand_ws if hand_ws.count(w) > 1})
    if dup:
        errors.append(f"交接给 QA 存在重复 WS 小节: {', '.join(dup)}")
    unknown = sorted(set(hand_ws) - proj_ws) if proj_ws else []
    if unknown:
        errors.append(f"交接给 QA 的 WS 未在 PROJECT §4 登记: {', '.join(unknown)}")
    return errors, warns


def _check_plan_gate(rd):
    errors, warns, oks = [], [], []
    for name in ("SPEC.md", "PROJECT.md", "ROUND-PLAN.md"):
        if not (rd / name).is_file():
            errors.append(f"PLAN-GATE: 缺文件 {name}")
    if errors:
        return errors, warns, oks
    text = (rd / "ROUND-PLAN.md").read_text(encoding="utf-8")
    vals = {}
    for key in PLAN_GATE_KEYS:
        m = re.search(rf"^{re.escape(key)}:\s*(.+)$", text, re.M)
        if not m or not m.group(1).strip():
            errors.append(f"PLAN-GATE: ROUND-PLAN.md 缺 {key}: 行")
        else:
            vals[key] = m.group(1).strip()
    contract = vals.get("contract", "")
    m = re.match(r"^([a-z]+)@(\d+\.\d+\.\d+)$", contract)
    if contract and not m:
        errors.append(f"PLAN-GATE: contract 格式应为 <type>@<x.y.z>，收到 {contract!r}")
    elif m:
        ctype, cver = m.groups()
        if ctype not in CONTRACT_TYPES:
            errors.append(f"PLAN-GATE: 未知 contract type {ctype!r}")
        elif not (TEMPLATES / "contracts" / ctype / "CONTRACT.md").is_file():
            errors.append(f"PLAN-GATE: 缺契约文件 templates/contracts/{ctype}/CONTRACT.md")
        else:
            frozen = (TEMPLATES / "contracts" / "VERSION").read_text(encoding="utf-8").strip()
            if cver != frozen:
                errors.append(f"PLAN-GATE: contract 版本 {cver} != 冻结版本 {frozen}")
            else:
                oks.append(f"PLAN-GATE: contract={contract} 与冻结版本一致")
    spec = _spec_declarations(rd / "SPEC.md")
    if not spec.get("baseline"):
        errors.append("PLAN-GATE: SPEC.md 缺 baseline: 声明")
    if not spec.get("contracts"):
        errors.append("PLAN-GATE: SPEC.md 缺 contracts: 声明")
    if not errors:
        oks.append("PLAN-GATE: 7/7 机械项齐备")
    return errors, warns, oks


def doctor(run_id, as_json=False, phase=None):
    errors, warns, oks = [], [], []
    rd = RUNS / run_id
    if not rd.exists():
        die(f"run 不存在: {rd}")
    if phase == "plan-gate":
        errors, warns, oks = _check_plan_gate(rd)
        return report(run_id, errors, warns, oks, as_json)

    for f in ["PROJECT.md", "DECISIONS.md", "ISSUES.xlsx"]:
        if not (rd / f).exists():
            errors.append(f"缺文件: {f}")
    st = latest_status(rd, required=False)
    if st is None:
        errors.append("缺文件: STATUS-Round-*.md")
    if errors:
        return report(run_id, errors, warns, oks, as_json)

    for doc in ["PROJECT", "DECISIONS", "STATUS"]:
        p = doc_path(rd, doc)
        h = read_header(p)
        if not h:
            errors.append(f"{p.name}: 缺 wf-doc 元信息块")
            continue
        if h.get("run") != run_id:
            errors.append(f"{p.name}: run 字段={h.get('run')} 与目录不符")
        if h.get("doc") != doc:
            errors.append(f"{p.name}: doc 字段={h.get('doc')} 应为 {doc}")
        if h.get("owner") != DOC_OWNER[doc]:
            warns.append(f"{p.name}: owner={h.get('owner')} 应为 {DOC_OWNER[doc]}")
        if h.get("state") not in DOC_ALLOWED[doc]:
            errors.append(f"{p.name}: state={h.get('state')} 非法")
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(h.get("updated", ""))):
            warns.append(f"{p.name}: updated={h.get('updated')} 不是 YYYY-MM-DD")
        for m in find_placeholders(p.read_text(encoding="utf-8")):
            warns.append(f"{p.name}: 还有未填占位符 {m.group(0)}")
            break
        if doc == "PROJECT":
            for key in ("tags", "primary_type", "maturity", "baseline", "contracts"):
                if not h.get(key):
                    warns.append(f"PROJECT.md: 缺 wf-doc 机器字段 {key}")
            spec_path = rd / "SPEC.md"
            if spec_path.is_file():
                decl = _spec_declarations(spec_path)
                for key in ("baseline", "contracts"):
                    if h.get(key) and decl.get(key) and h.get(key) != decl.get(key):
                        errors.append(
                            f"PROJECT.md: wf-doc {key}={h.get(key)!r} 与 SPEC §0 {decl.get(key)!r} 不一致"
                        )

    # PROJECT 状态相关
    ph = read_header(rd / "PROJECT.md")
    body6 = section((rd / "PROJECT.md").read_text(encoding="utf-8"), "## 6.", "## 7.")
    proj_text = (rd / "PROJECT.md").read_text(encoding="utf-8")
    if ph.get("state") in ("plan-ready", "waiting-main", "closed"):
        m = find_placeholders(proj_text)[0] if find_placeholders(proj_text) else None
        if m:
            errors.append(
                f"PROJECT.state={ph.get('state')} 但还有未填占位符 {m.group(0)}"
            )
    if ph.get("state") == "waiting-main":
        if len(body6) < 200 or find_placeholders(body6):
            errors.append(
                "PROJECT.state=waiting-main，但 §6 上报区为空/未填（主会话无从拍板）"
            )
        else:
            oks.append("PROJECT §6 上报区已填，可交主会话")
    if ph.get("state") == "closed":
        oks.append("PROJECT 已 closed")

    # STATUS 状态相关
    sh = read_header(st)
    text = st.read_text(encoding="utf-8")
    progress = section(text, "<!-- wf:progress:start -->", "<!-- wf:progress:end -->")
    prows = [
        l for l in progress.splitlines() if l.strip().startswith("|") and "---" not in l
    ]
    data_rows = [l for l in prows if "时间" not in l]
    if not data_rows:
        warns.append(f"{st.name}: 还没有进度条目")
    for l in data_rows:
        if l.count("|") < 6:
            errors.append(f"{st.name}: 进度行缺列: {l[:60]}")
    if sh.get("state") in ("qa-pending", "qa-done", "closed"):
        hand = section(text, "## 交接给 QA", "<!-- wf:handoff:start -->")
        hand = re.sub(r"[>\s\-*]", "", hand)
        if len(hand) < 40:
            errors.append(f"{st.name}: state={sh.get('state')} 但「交接给 QA」为空")
        else:
            oks.append("交接给 QA 已填")
    if sh.get("state") == "tdo-in-progress":
        oks.append(f"{st.name}: TDO 执行中（{len(data_rows)} 条进度）")
    bind_errors, bind_warns = _status_binding_checks(proj_text, text)
    errors.extend(bind_errors)
    warns.extend(bind_warns)
    if not bind_errors:
        oks.append(f"{st.name}: WS/交接绑定检查通过")

    shard_files = sorted((rd / "status-shards").glob("*.jsonl")) if (rd / "status-shards").is_dir() else []
    if shard_files:
        warns.append(f"还有 {len(shard_files)} 个未合并的 STATUS shard 文件")
    else:
        oks.append("STATUS shards 已合并/无待合并")

    # 锁
    lk = read_lock(rd)
    if lk:
        tag = "已过期（可 --steal）" if lk.get("stale") else "活跃"
        (warns if lk.get("stale") else warns).append(
            f"STATUS 锁存在且{tag}：持有者={lk.get('agent')}，锁龄={lk.get('age')}s"
        )

    # DECISIONS / ISSUES
    dec_ids = set(
        re.findall(r"\bD-\d{3}\b", (rd / "DECISIONS.md").read_text(encoding="utf-8"))
    )
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import issues as issues_mod

        ledger_rows = issues_mod.read_rows(rd / "ISSUES.xlsx")
        open_s1s2 = 0
        for row in ledger_rows:
            g = lambda h: row.get(h)
            iid = g("ID")
            if not iid:
                continue
            if g("类型") not in issues_mod.TYPES:
                errors.append(f"ISSUES {iid}: 类型非法 {g('类型')!r}")
            if g("严重度") not in issues_mod.SEV:
                errors.append(f"ISSUES {iid}: 严重度非法 {g('严重度')!r}")
            if g("状态") not in issues_mod.STATUSES:
                errors.append(f"ISSUES {iid}: 状态非法 {g('状态')!r}")
            if not g("来源"):
                errors.append(f"ISSUES {iid}: 缺来源")
            if not g("建议动作"):
                errors.append(f"ISSUES {iid}: 缺建议动作")
            if g("严重度") == "S1" and g("需主会话决策") != "是":
                errors.append(f"ISSUES {iid}: S1 必须“需主会话决策=是”")
            dec = g("关联决策ID")
            if dec and str(dec).strip() and str(dec).strip() not in dec_ids:
                errors.append(f"ISSUES {iid}: 关联决策 {dec} 在 DECISIONS.md 中不存在")
            if str(g("状态")) not in ("已关闭", "挂起") and g("严重度") in ("S1", "S2"):
                open_s1s2 += 1
        oks.append(f"ISSUES 已登记（open S1/S2={open_s1s2}）")
        if open_s1s2:
            warns.append(f"还有 {open_s1s2} 条未关闭的 S1/S2（达成前必须清零）")
    except SystemExit:
        raise
    except Exception as e:
        errors.append(f"ISSUES.xlsx 读取失败: {e}")

    if dec_ids:
        oks.append(f"DECISIONS 已记 {len(dec_ids)} 条")

    # 安全门控（仅启用了 safety/config.json 的 run）
    safety_cfg = rd / "safety" / "config.json"
    if safety_cfg.exists():
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            import hdrive_gate as hg

            old_runs = hg.RUNS
            hg.RUNS = RUNS
            try:
                sdata = hg.status_data(run_id)
            finally:
                hg.RUNS = old_runs
            ss = sdata["summary"]
            oks.append(
                "安全门控账本: actions={actions} gate_pass={gate_pass} "
                "gate_fail={gate_fail} safety_pending={safety_pending} "
                "executed_ok={executed_ok} executed_bad={executed_bad}".format(**ss)
            )
            closed_stage = sh.get("state") in ("qa-pending", "qa-done", "closed") or ph.get(
                "state"
            ) in ("waiting-main", "closed")
            if ss["ungated"]:
                msg = f"安全门控还有 {ss['ungated']} 个 action 未 gate"
                (errors if closed_stage else warns).append(msg)
            if ss["safety_pending"]:
                msg = (
                    f"安全门控还有 {ss['safety_pending']} 个 FAIL action 未逐条 SAFETY 审核"
                )
                (errors if closed_stage else warns).append(msg)
            for row in sdata["rows"]:
                executed = row["execution"] not in ("-",)
                if not executed:
                    continue
                if row["gate"] != "PASS" and row["review"] != "approve":
                    errors.append(
                        f"安全事件 {row['action_id']}: 无 PASS/安全 approve 却存在执行记录 "
                        f"(gate={row['gate']}, review={row['review']})"
                    )
                if row["risk"] == "red" and row["human"] in ("-", "PENDING"):
                    errors.append(
                        f"安全事件 {row['action_id']}: red 动作无独立人工批准却存在执行记录"
                    )
        except SystemExit:
            raise
        except Exception as e:
            errors.append(f"safety 账本读取失败: {e}")

    return report(run_id, errors, warns, oks, as_json)


def report(run_id, errors, warns, oks, as_json):
    if as_json:
        print(
            json.dumps(
                {"run": run_id, "errors": errors, "warns": warns, "ok": oks},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(f"== doctor: {run_id} ==")
        for x in errors:
            print(f"[ERROR] {x}")
        for x in warns:
            print(f"[WARN ] {x}")
        for x in oks:
            print(f"[OK   ] {x}")
        print(
            f"结果: {'FAIL' if errors else 'PASS'} "
            f"(errors={len(errors)}, warns={len(warns)})"
        )
    return 1 if errors else 0


# ------------------------------------------------------------------ main
def main():
    p = argparse.ArgumentParser(description="工作流组编排器")
    sub = p.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("new-run")
    q.add_argument("run_id")
    q.add_argument("--goal", default="")
    q.add_argument("--goal-file", default="")
    q.add_argument("--project-root", default="")
    q.add_argument("--scope", default="")
    q.add_argument("--template", default="", help="领域特化 run 模板目录（templates/specialized/*；默认 templates/）")
    q.add_argument("--project-name", default="")
    q.add_argument("--tdo", type=int, default=2)
    q.add_argument("--force", action="store_true")
    q.set_defaults(fn=cmd_new_run)

    q = sub.add_parser("new-round")
    q.add_argument("run_id")
    q.set_defaults(fn=cmd_new_round)

    q = sub.add_parser("state")
    q.add_argument("run_id")
    q.add_argument("doc")
    q.add_argument("new_state")
    q.add_argument(
        "--by",
        default="",
        help="执行者角色 MAIN/PMO/TDO/QA/SAFETY；关键迁移必填",
    )
    q.set_defaults(fn=cmd_state)

    q = sub.add_parser("brief")
    q.add_argument(
        "--role", required=True, choices=["pmo", "tdo", "qa", "safety"]
    )
    q.add_argument("--run", required=True)
    q.add_argument("--agent", default="")
    q.set_defaults(fn=cmd_brief)

    q = sub.add_parser("lock")
    q.add_argument("run_id")
    q.add_argument("--agent", required=True)
    q.add_argument("--wait", type=int, default=LOCK_WAIT)
    q.add_argument("--steal", action="store_true")

    def _lock(a):
        if acquire_lock(run_dir(a.run_id), a.agent, a.wait, a.steal):
            print("[OK] 已加锁；写完后 unlock（或直接用 append-status 自动管理）")
            return 0
        print("[LOCK] 未取得锁", file=sys.stderr)
        return 4

    q.set_defaults(fn=_lock)

    q = sub.add_parser("unlock")
    q.add_argument("run_id")
    q.add_argument("--agent", default="")
    q.add_argument("--force", action="store_true")
    q.set_defaults(
        fn=lambda a: release_lock(run_dir(a.run_id), a.agent, a.force) and None
    )

    q = sub.add_parser("lock-status")
    q.add_argument("run_id")

    def _ls(a):
        m = read_lock(run_dir(a.run_id))
        print(json.dumps(m, ensure_ascii=False, indent=2) if m else "(无锁)")

    q.set_defaults(fn=_ls)

    q = sub.add_parser("append-status")
    q.add_argument("run_id")
    q.add_argument("--agent", required=True)
    q.add_argument("--ws", required=True)
    q.add_argument("--action", required=True)
    q.add_argument("--evidence", required=True)
    q.add_argument("--state", default="完成")
    q.add_argument("--blocker", default="")
    q.add_argument("--also", action="append", default=[])
    q.add_argument("--no-commit", dest="commit", action="store_false")
    q.add_argument("--wait", type=int, default=LOCK_WAIT)
    q.add_argument("--steal", action="store_true")
    q.set_defaults(fn=cmd_append_status, commit=True)

    q = sub.add_parser("append-shard")
    q.add_argument("run_id")
    q.add_argument("--agent", required=True)
    q.add_argument("--ws", required=True)
    q.add_argument("--action", required=True)
    q.add_argument("--evidence", required=True)
    q.add_argument("--state", default="完成")
    q.add_argument("--blocker", default="")
    q.set_defaults(fn=cmd_append_shard)

    q = sub.add_parser("merge-shards")
    q.add_argument("run_id")
    q.add_argument("--agent", default="merge-shards")
    q.add_argument("--wait", type=int, default=LOCK_WAIT)
    q.add_argument("--steal", action="store_true")
    q.set_defaults(fn=cmd_merge_shards)

    q = sub.add_parser("serve")
    q.add_argument("action", choices=["start", "stop", "status"])
    q.add_argument("--port", type=int, default=0)
    q.add_argument("--dir", default="")
    q.add_argument(
        "--impure", action="store_true", help="禁用 --pure（需要外部插件/MCP 时）"
    )
    q.set_defaults(fn=cmd_serve)

    q = sub.add_parser("delegate")
    q.add_argument("run_id")
    q.add_argument(
        "--role", required=True, choices=["pmo", "tdo", "qa", "safety"]
    )
    q.add_argument("--name", default="")
    q.add_argument("--ws", default="")
    q.add_argument("--model", default="")
    q.add_argument("--oc-agent", default=OC_AGENT)
    q.add_argument("--backend", choices=DELEGATE_BACKENDS, default="auto")
    q.add_argument("--server", default="")
    q.add_argument("--port", type=int, default=0)
    q.add_argument("--timeout", type=int, default=900)
    q.add_argument(
        "--heartbeat", type=int, default=60, help="send 期间心跳间隔秒数（S-2）"
    )
    q.add_argument("--dry-run", action="store_true")
    q.add_argument("--force", action="store_true")
    q.set_defaults(fn=cmd_delegate)

    q = sub.add_parser("squad")
    q.add_argument("run_id")
    q.add_argument("--role", default="tdo", choices=["tdo"])
    q.add_argument(
        "--agents",
        required=True,
        help="格式: tdo-a1:WS-1,tdo-a2:WS-2（每个执行体必须带 WS）",
    )
    q.add_argument("--model", default="")
    q.add_argument("--oc-agent", default=OC_AGENT)
    q.add_argument("--backend", choices=DELEGATE_BACKENDS, default="auto")
    q.add_argument("--server", default="")
    q.add_argument("--port", type=int, default=0)
    q.add_argument("--timeout", type=int, default=3600)
    q.add_argument(
        "--heartbeat", type=int, default=60, help="send 期间心跳间隔秒数（S-2）"
    )
    q.add_argument("--jobs", type=int, default=6)
    q.add_argument("--dry-run", action="store_true")
    q.add_argument("--force", action="store_true")
    q.add_argument("--skip-resource-check", action="store_true")
    q.set_defaults(fn=cmd_squad)

    q = sub.add_parser("resource-check")
    q.add_argument("--agents", type=int, default=1)
    q.add_argument("--force", action="store_true")
    q.add_argument("--json", action="store_true")
    q.set_defaults(fn=cmd_resource_check)

    q = sub.add_parser("ledger")
    q.add_argument("run_id")
    q.set_defaults(fn=cmd_ledger)

    q = sub.add_parser("commit-run")
    q.add_argument("run_id")
    q.add_argument("--message", default="")
    q.add_argument("--also", action="append", default=[])
    q.add_argument("--dry-run", action="store_true")
    q.set_defaults(fn=cmd_commit_run)

    q = sub.add_parser("commit")
    q.add_argument("--repo", required=True)
    q.add_argument("--run", required=True)
    q.add_argument("--round", type=int, default=0)
    q.add_argument("--message", required=True)
    q.add_argument("paths", nargs="*")
    q.set_defaults(fn=cmd_commit)

    q = sub.add_parser("doctor")
    q.add_argument("run_id")
    q.add_argument("--json", action="store_true")
    q.add_argument("--phase", choices=["plan-gate"], default=None)
    q.set_defaults(fn=lambda a: sys.exit(doctor(a.run_id, a.json, a.phase)))

    q = sub.add_parser("sync-contracts")
    q.add_argument("run_id")
    q.set_defaults(fn=cmd_sync_contracts)

    q = sub.add_parser("evidence-pack")
    q.add_argument("run_id")
    q.add_argument("--out", default="")
    q.add_argument("--pytest", action="store_true")
    q.add_argument("--test-timeout", type=int, default=900)
    q.add_argument("--json", action="store_true")
    q.set_defaults(fn=cmd_evidence_pack)

    q = sub.add_parser("status-all")
    q.add_argument("--json", action="store_true")
    q.set_defaults(fn=cmd_status_all)

    q = sub.add_parser("overview")
    q.add_argument("--json", action="store_true")
    q.set_defaults(fn=cmd_status_all)

    args = p.parse_args()
    r = args.fn(args)
    if isinstance(r, int):
        sys.exit(r)


if __name__ == "__main__":
    main()
