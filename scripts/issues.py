#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""issues.py — ISSUES.xlsx 读写（QA 新增 / PMO 收轮改状态 / 人查 / doctor 复用）

用法:
  python3 issues.py init   <xlsx>
  python3 issues.py add    <xlsx> --round N --type 风险 --title "..." [--desc ...]
                                   [--severity S2] [--owner PMO] [--source "..."]
                                   [--action "..."] [--need-decision yes|no]
  python3 issues.py list   <xlsx> [--open-only] [--round N] [--severity S1] [--json]
  python3 issues.py update <xlsx> <ID> [--status ...] [--owner ...] [--severity ...]
                                   [--action ...] [--decision D-001] [--desc ...] [--title ...]
  python3 issues.py close  <xlsx> <ID> --decision D-002
  python3 issues.py export <xlsx> [--out file.csv]

硬规则:
  - ID 由本脚本分配（P-/R-/C- 前缀），不要手编。
  - S1 行必须“需主会话决策=是”。
  - 行只增不删；作废改状态。修改一律走本脚本，不要手编 xlsx。
依赖: openpyxl 可选；未安装时读写同目录 ISSUES.jsonl 降级（xlsx 写入不可用）。
"""
import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.formatting.rule import FormulaRule
    from openpyxl.worksheet.datavalidation import DataValidation

    HAS_OPENPYXL = True
except ImportError:  # pragma: no cover - exercised via monkeypatch/CI without openpyxl
    Workbook = load_workbook = None
    Alignment = Border = Font = PatternFill = Side = FormulaRule = DataValidation = None
    HAS_OPENPYXL = False

SHEET = "账本"
SHEET_SUM = "汇总"
SHEET_HELP = "说明"
HEADERS = ["ID", "轮次", "类型", "标题", "描述", "严重度", "状态", "责任角色",
           "来源", "建议动作", "需主会话决策", "关联决策ID", "创建时间", "更新时间"]
COL = {h: i + 1 for i, h in enumerate(HEADERS)}
NC = len(HEADERS)
MAXROW = 1000

TYPES = ["问题", "风险", "变更"]
SEV = ["S1", "S2", "S3", "S4"]
STATUSES = ["新建", "处理中", "待主会话", "已决议", "已关闭", "挂起"]
OWNERS = ["PMO", "TDO", "QA", "主会话"]
PREFIX = {"问题": "P", "风险": "R", "变更": "C"}
SEV_DESC = {
    "S1": "阻塞：本轮结果不可用或无法继续；必须标“需主会话决策=是”",
    "S2": "重要：影响质量或下轮计划；收轮前 PMO 必须处置",
    "S3": "一般：可带着走，下轮或收尾处理",
    "S4": "提示：记录备查",
}

THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(vertical="top", wrap_text=True)


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def die(msg, code=1):
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(code)


def load(path: Path):
    if not HAS_OPENPYXL:
        die(f"openpyxl 不可用，无法按 xlsx 对象读取 {path}；请用 read_rows()/JSONL 降级路径")
    if not path.exists():
        die(f"文件不存在: {path}")
    wb = load_workbook(path)
    if SHEET not in wb.sheetnames:
        die(f"{path} 缺少 sheet「{SHEET}」（可能不是 ISSUES 模板）")
    return wb


def jsonl_path(path: Path) -> Path:
    """Sibling JSONL mirror for an ISSUES.xlsx path."""
    return Path(path).with_suffix(".jsonl")


def _row_dict(ws, r: int) -> dict:
    return {h: ws.cell(row=r, column=COL[h]).value for h in HEADERS}


def _rows_from_ws(ws) -> list[dict]:
    rows = []
    for r in range(2, ws.max_row + 1):
        if ws.cell(row=r, column=COL["ID"]).value:
            rows.append(_row_dict(ws, r))
    return rows


def write_jsonl_rows(path: Path, rows: list[dict]) -> None:
    path = jsonl_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for row in rows:
            normalized = {h: row.get(h, "") for h in HEADERS}
            f.write(json.dumps(normalized, ensure_ascii=False, default=str) + "\n")
    os.replace(tmp, path)


def read_jsonl_rows(path: Path) -> list[dict]:
    p = jsonl_path(path)
    if not p.exists():
        return []
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if isinstance(row, dict):
            rows.append({h: row.get(h, "") for h in HEADERS})
    return rows


def sync_jsonl(path: Path, ws) -> Path:
    out = jsonl_path(path)
    write_jsonl_rows(out, _rows_from_ws(ws))
    return out


def read_rows(path: Path) -> list[dict]:
    """Read ISSUES rows from xlsx when possible, else from the JSONL mirror.

    Writers always refresh the JSONL mirror. If openpyxl is unavailable but a
    mirror exists, consumers such as `wf.py doctor` keep working in degraded
    mode. A missing ledger is still a hard error.
    """
    path = Path(path)
    if HAS_OPENPYXL and path.exists():
        return _rows_from_ws(load(path)[SHEET])
    rows = read_jsonl_rows(path)
    if rows or jsonl_path(path).exists():
        return rows
    if not path.exists():
        die(f"文件不存在: {path}（也没有 {jsonl_path(path).name} 降级镜像）")
    die(f"{path} 存在但 openpyxl 不可用，且没有 {jsonl_path(path).name} 镜像")


def next_id_rows(rows: list[dict], prefix: str) -> str:
    mx = 0
    for row in rows:
        s = str(row.get("ID") or "").strip().upper()
        if s.startswith(prefix + "-"):
            try:
                mx = max(mx, int(s.split("-", 1)[1]))
            except ValueError:
                pass
    return f"{prefix}-{mx + 1:03d}"


def find_row(ws, issue_id):
    for r in range(2, ws.max_row + 1):
        v = ws.cell(row=r, column=COL["ID"]).value
        if v and str(v).strip().upper() == issue_id.strip().upper():
            return r
    return None


def next_id(ws, prefix):
    mx = 0
    for r in range(2, ws.max_row + 1):
        v = ws.cell(row=r, column=COL["ID"]).value
        if v:
            s = str(v).strip().upper()
            if s.startswith(prefix + "-"):
                try:
                    mx = max(mx, int(s.split("-", 1)[1]))
                except ValueError:
                    pass
    return f"{prefix}-{mx + 1:03d}"


def style_row(ws, r):
    for c in range(1, NC + 1):
        cell = ws.cell(row=r, column=c)
        cell.border = BORDER
        cell.alignment = WRAP


def ensure_enum(value, allowed, field):
    if value is None or str(value).strip() == "":
        return ""
    if value not in allowed:
        die(f"{field} 非法: {value!r}，允许值: {' / '.join(allowed)}")
    return value


# ---------------------------------------------------------------- init
def cmd_init(args):
    path = Path(args.xlsx)
    mirror = jsonl_path(path)
    if (path.exists() or mirror.exists()) and not args.force:
        die(f"{path} 或 {mirror.name} 已存在；要重建请加 --force")
    if not HAS_OPENPYXL:
        write_jsonl_rows(path, [])
        print(f"[WARN] openpyxl 不可用；已创建 JSONL 降级账本: {mirror}")
        return
    wb = Workbook()
    ws = wb.active
    ws.title = SHEET

    head_fill = PatternFill("solid", fgColor="1F4E78")
    head_font = Font(color="FFFFFF", bold=True, size=11)
    for i, h in enumerate(HEADERS, start=1):
        c = ws.cell(row=1, column=i, value=h)
        c.fill = head_fill
        c.font = head_font
        c.alignment = Alignment(vertical="center", horizontal="center", wrap_text=True)
        c.border = BORDER
    widths = {"ID": 8, "轮次": 6, "类型": 6, "标题": 24, "描述": 40, "严重度": 7,
              "状态": 9, "责任角色": 9, "来源": 22, "建议动作": 32,
              "需主会话决策": 12, "关联决策ID": 11, "创建时间": 16, "更新时间": 16}
    for h, w in widths.items():
        ws.column_dimensions[chr(64 + COL[h])].width = w
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{chr(64 + NC)}{MAXROW}"

    def dv(formula, cols):
        d = DataValidation(type="list", formula1=formula, allow_blank=True, showErrorMessage=True)
        ws.add_data_validation(d)
        for col in cols:
            d.add(f"{col}2:{col}{MAXROW}")

    dv('"' + ",".join(TYPES) + '"', ["C"])
    dv('"' + ",".join(SEV) + '"', ["F"])
    dv('"' + ",".join(STATUSES) + '"', ["G"])
    dv('"' + ",".join(OWNERS) + '"', ["H"])
    dv('"是,否"', ["K"])

    red = PatternFill("solid", fgColor="FFC7CE")
    orange = PatternFill("solid", fgColor="FFEB9C")
    green = PatternFill("solid", fgColor="C6EFCE")
    yellow = PatternFill("solid", fgColor="FFF2CC")
    rng = f"A2:{chr(64 + NC)}{MAXROW}"
    ws.conditional_formatting.add(rng, FormulaRule(formula=['$F2="S1"'], fill=red))
    ws.conditional_formatting.add(rng, FormulaRule(formula=['$F2="S2"'], fill=orange))
    ws.conditional_formatting.add(rng, FormulaRule(formula=['$G2="已关闭"'], fill=green))
    ws.conditional_formatting.add(rng, FormulaRule(formula=['$K2="是"'], fill=yellow))

    # 汇总
    sm = wb.create_sheet(SHEET_SUM)
    sm.column_dimensions["A"].width = 22
    sm.column_dimensions["B"].width = 10
    rows = [
        ("指标", "数量"),
        ("总行数", f"=COUNTA({SHEET}!$A$2:$A${MAXROW})"),
        ("", ""),
        ("按严重度", ""),
        ("S1", f'=COUNTIF({SHEET}!$F$2:$F${MAXROW},"S1")'),
        ("S2", f'=COUNTIF({SHEET}!$F$2:$F${MAXROW},"S2")'),
        ("S3", f'=COUNTIF({SHEET}!$F$2:$F${MAXROW},"S3")'),
        ("S4", f'=COUNTIF({SHEET}!$F$2:$F${MAXROW},"S4")'),
        ("", ""),
        ("按状态", ""),
        ("新建", f'=COUNTIF({SHEET}!$G$2:$G${MAXROW},"新建")'),
        ("处理中", f'=COUNTIF({SHEET}!$G$2:$G${MAXROW},"处理中")'),
        ("待主会话", f'=COUNTIF({SHEET}!$G$2:$G${MAXROW},"待主会话")'),
        ("已决议", f'=COUNTIF({SHEET}!$G$2:$G${MAXROW},"已决议")'),
        ("已关闭", f'=COUNTIF({SHEET}!$G$2:$G${MAXROW},"已关闭")'),
        ("挂起", f'=COUNTIF({SHEET}!$G$2:$G${MAXROW},"挂起")'),
        ("", ""),
        ("按类型", ""),
        ("问题", f'=COUNTIF({SHEET}!$C$2:$C${MAXROW},"问题")'),
        ("风险", f'=COUNTIF({SHEET}!$C$2:$C${MAXROW},"风险")'),
        ("变更", f'=COUNTIF({SHEET}!$C$2:$C${MAXROW},"变更")'),
        ("", ""),
        ("需主会话决策", f'=COUNTIF({SHEET}!$K$2:$K${MAXROW},"是")'),
        ("未关闭 S1", f'=COUNTIFS({SHEET}!$F$2:$F${MAXROW},"S1",{SHEET}!$G$2:$G${MAXROW},"<>已关闭")'),
    ]
    for i, (a, b) in enumerate(rows, start=1):
        sm.cell(row=i, column=1, value=a).font = Font(bold=(b == "" or a in ("指标",)))
        sm.cell(row=i, column=2, value=b)

    # 说明
    hp = wb.create_sheet(SHEET_HELP)
    hp.column_dimensions["A"].width = 110
    lines = [
        "ISSUES — 问题 / 风险 / 变更 台账（QA 写，PMO 收轮处置）",
        "",
        "写者：QA 新增行（ID 自动分配）；PMO 收轮时只更新状态列。其他角色只读。",
        "修改一律用：python3 scripts/issues.py add|update|list|close —— 不要手编本文件。",
        "",
        "字段字典：",
        "  ID            脚本分配。P- 问题 / R- 风险 / C- 变更，只增不删。",
        "  轮次          发现于第几轮（整数）。",
        "  类型          问题（已发生缺陷）/ 风险（未发生但可能）/ 变更（范围或计划变化）。",
        "  严重度        S1 阻塞 / S2 重要 / S3 一般 / S4 提示。",
        "  状态          新建 / 处理中 / 待主会话 / 已决议 / 已关闭 / 挂起。",
        "  责任角色      PMO / TDO / QA / 主会话。",
        "  来源          必须可回溯：如 STATUS-Round-1.md#进度条目 或 文件路径#章节。",
        "  建议动作      一句话可执行，禁止“需进一步分析”式空话。",
        "  需主会话决策  是 / 否；S1 行必须为“是”。",
        "  关联决策ID    主会话在 DECISIONS.md 的 D-xxx（决议/关闭后回填）。",
        "",
        "严重度定义：",
    ]
    lines += [f"  {k}  {v}" for k, v in SEV_DESC.items()]
    lines += [
        "",
        "硬规则：",
        "  1) S1 行必须“需主会话决策=是”（doctor 会检查）。",
        "  2) 行只增不删；作废改状态，历史保留。",
        "  3) 无来源、无建议动作的行视为无效登记。",
        "  4) 同一 xlsx 不要两个进程同时写（脚本会报错）。",
    ]
    for i, t in enumerate(lines, start=1):
        hp.cell(row=i, column=1, value=t).alignment = Alignment(vertical="top", wrap_text=False)

    wb.save(path)
    write_jsonl_rows(path, [])
    print(f"[OK] 已生成 ISSUES 模板: {path}")


# ---------------------------------------------------------------- add
def cmd_add(args):
    path = Path(args.xlsx)
    if not HAS_OPENPYXL:
        rows = read_jsonl_rows(path)
        itype = ensure_enum(args.type, TYPES, "--type")
        sev = ensure_enum(args.severity, SEV, "--severity")
        status = ensure_enum(args.status, STATUSES, "--status")
        owner = ensure_enum(args.owner, OWNERS, "--owner")
        need = "是" if args.need_decision in ("yes", "是", True) else "否"
        if sev == "S1" and need != "是" and not args.force:
            die("S1 行必须 --need-decision yes（规则见模板说明页）")
        if not args.source.strip():
            die("--source 不能为空：必须可回溯（STATUS 行 / 文件路径#章节）")
        if not args.action.strip():
            die("--action 不能为空：写一句话可执行动作")
        iid = next_id_rows(rows, PREFIX[itype]) if not args.id else args.id
        ts = now_str()
        rows.append({
            "ID": iid, "轮次": int(args.round), "类型": itype, "标题": args.title,
            "描述": args.desc, "严重度": sev, "状态": status, "责任角色": owner,
            "来源": args.source, "建议动作": args.action, "需主会话决策": need,
            "关联决策ID": "", "创建时间": ts, "更新时间": ts,
        })
        write_jsonl_rows(path, rows)
        print(f"[OK] 新增 {iid} · {itype} · {sev} · {args.title}（JSONL 降级）")
        return
    wb = load(path)
    ws = wb[SHEET]
    r = ws.max_row + 1 if ws.max_row >= 1 and ws.cell(row=2, column=1).value else 2
    while ws.cell(row=r, column=COL["ID"]).value:
        r += 1

    itype = ensure_enum(args.type, TYPES, "--type")
    sev = ensure_enum(args.severity, SEV, "--severity")
    status = ensure_enum(args.status, STATUSES, "--status")
    owner = ensure_enum(args.owner, OWNERS, "--owner")
    need = "是" if args.need_decision in ("yes", "是", True) else "否"
    if sev == "S1" and need != "是" and not args.force:
        die("S1 行必须 --need-decision yes（规则见模板说明页）")
    if not args.source.strip():
        die("--source 不能为空：必须可回溯（STATUS 行 / 文件路径#章节）")
    if not args.action.strip():
        die("--action 不能为空：写一句话可执行动作")

    iid = next_id(ws, PREFIX[itype]) if not args.id else args.id
    ts = now_str()
    values = [iid, int(args.round), itype, args.title, args.desc, sev, status,
              owner, args.source, args.action, need, "", ts, ts]
    for c, v in enumerate(values, start=1):
        ws.cell(row=r, column=c, value=v)
    style_row(ws, r)
    wb.save(path)
    sync_jsonl(path, ws)
    print(f"[OK] 新增 {iid} · {itype} · {sev} · {args.title}")


# ---------------------------------------------------------------- list
def cmd_list(args):
    path = Path(args.xlsx)
    rows = []
    for row in read_rows(path):
        if not row.get("ID"):
            continue
        if args.open_only and str(row.get("状态")) in ("已关闭",):
            continue
        if args.round is not None and str(row.get("轮次")) != str(args.round):
            continue
        if args.severity and str(row.get("严重度")) != args.severity:
            continue
        if args.need_decision and str(row.get("需主会话决策")) != args.need_decision:
            continue
        rows.append(dict(row))
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2, default=str))
        return
    if not rows:
        print("(无匹配行)")
        return
    print(f"{'ID':<7}{'轮':<4}{'类型':<5}{'严重度':<6}{'状态':<7}{'决策':<4}标题")
    for x in rows:
        print(f"{str(x['ID']):<7}{str(x['轮次']):<4}{str(x['类型']):<5}"
              f"{str(x['严重度']):<6}{str(x['状态']):<7}{str(x['需主会话决策']):<4}{x['标题']}")


# ---------------------------------------------------------------- update / close
def cmd_update(args):
    path = Path(args.xlsx)
    if not HAS_OPENPYXL:
        rows = read_jsonl_rows(path)
        target = next(
            (x for x in rows if str(x.get("ID") or "").strip().upper() == args.id.strip().upper()),
            None,
        )
        if target is None:
            die(f"找不到 ID: {args.id}")
        mapping = {
            "status": ("状态", STATUSES), "owner": ("责任角色", OWNERS),
            "severity": ("严重度", SEV), "action": ("建议动作", None),
            "decision": ("关联决策ID", None), "desc": ("描述", None),
            "title": ("标题", None),
        }
        changed = []
        for field, (header, allowed) in mapping.items():
            val = getattr(args, field)
            if val is None:
                continue
            if allowed:
                val = ensure_enum(val, allowed, f"--{field}")
            target[header] = val
            changed.append(f"{header}={val}")
        if not changed:
            die("没有指定要修改的字段（见 --help）")
        target["更新时间"] = now_str()
        if target.get("严重度") == "S1" and target.get("需主会话决策") == "否":
            print("[WARN] 该行是 S1 但“需主会话决策=否”，请同时修正 K 列（doctor 会报错）")
        write_jsonl_rows(path, rows)
        print(f"[OK] {args.id} 更新: {', '.join(changed)}（JSONL 降级）")
        return
    wb = load(path)
    ws = wb[SHEET]
    r = find_row(ws, args.id)
    if r is None:
        die(f"找不到 ID: {args.id}")
    mapping = {
        "status": ("状态", STATUSES), "owner": ("责任角色", OWNERS),
        "severity": ("严重度", SEV), "action": ("建议动作", None),
        "decision": ("关联决策ID", None), "desc": ("描述", None), "title": ("标题", None),
    }
    changed = []
    for field, (header, allowed) in mapping.items():
        val = getattr(args, field)
        if val is None:
            continue
        if allowed:
            val = ensure_enum(val, allowed, f"--{field}")
        ws.cell(row=r, column=COL[header], value=val)
        changed.append(f"{header}={val}")
    if not changed:
        die("没有指定要修改的字段（见 --help）")
    if args.status == "S1":
        pass
    ws.cell(row=r, column=COL["更新时间"], value=now_str())
    if ws.cell(row=r, column=COL["严重度"]).value == "S1" and \
       ws.cell(row=r, column=COL["需主会话决策"]).value == "否":
        print("[WARN] 该行是 S1 但“需主会话决策=否”，请同时修正 K 列（doctor 会报错）")
    wb.save(path)
    sync_jsonl(path, ws)
    print(f"[OK] {args.id} 更新: {', '.join(changed)}")


def cmd_close(args):
    path = Path(args.xlsx)
    if not args.decision:
        die("关闭必须给 --decision D-xxx（对应 DECISIONS.md 的决策）")
    if not HAS_OPENPYXL:
        rows = read_jsonl_rows(path)
        target = next(
            (x for x in rows if str(x.get("ID") or "").strip().upper() == args.id.strip().upper()),
            None,
        )
        if target is None:
            die(f"找不到 ID: {args.id}")
        target["状态"] = "已关闭"
        target["关联决策ID"] = args.decision
        target["更新时间"] = now_str()
        write_jsonl_rows(path, rows)
        print(f"[OK] {args.id} 已关闭（{args.decision}，JSONL 降级）")
        return
    wb = load(path)
    ws = wb[SHEET]
    r = find_row(ws, args.id)
    if r is None:
        die(f"找不到 ID: {args.id}")
    ws.cell(row=r, column=COL["状态"], value="已关闭")
    ws.cell(row=r, column=COL["关联决策ID"], value=args.decision)
    ws.cell(row=r, column=COL["更新时间"], value=now_str())
    wb.save(path)
    sync_jsonl(path, ws)
    print(f"[OK] {args.id} 已关闭（{args.decision}）")


# ---------------------------------------------------------------- export
def cmd_export(args):
    path = Path(args.xlsx)
    out = []
    for row in read_rows(path):
        if not row.get("ID"):
            continue
        out.append([row.get(h, "") for h in HEADERS])
    if args.out:
        with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(HEADERS)
            w.writerows(out)
        print(f"[OK] 导出 {len(out)} 行 → {args.out}")
    else:
        w = csv.writer(sys.stdout)
        w.writerow(HEADERS)
        w.writerows(out)


def main():
    p = argparse.ArgumentParser(description="ISSUES.xlsx 读写工具")
    sub = p.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("init", help="生成模板")
    q.add_argument("xlsx")
    q.add_argument("--force", action="store_true")
    q.set_defaults(fn=cmd_init)

    q = sub.add_parser("add", help="新增一行")
    q.add_argument("xlsx")
    q.add_argument("--round", required=True, type=int)
    q.add_argument("--type", required=True, choices=TYPES)
    q.add_argument("--title", required=True)
    q.add_argument("--desc", default="")
    q.add_argument("--severity", default="S3", choices=SEV)
    q.add_argument("--status", default="新建", choices=STATUSES)
    q.add_argument("--owner", default="PMO", choices=OWNERS)
    q.add_argument("--source", required=True)
    q.add_argument("--action", required=True)
    q.add_argument("--need-decision", default="no", choices=["yes", "no", "是", "否"])
    q.add_argument("--id", default=None, help=argparse.SUPPRESS)
    q.add_argument("--force", action="store_true")
    q.set_defaults(fn=cmd_add)

    q = sub.add_parser("list", help="列出")
    q.add_argument("xlsx")
    q.add_argument("--open-only", action="store_true")
    q.add_argument("--round", type=int)
    q.add_argument("--severity", choices=SEV)
    q.add_argument("--need-decision", choices=["是", "否"])
    q.add_argument("--json", action="store_true")
    q.set_defaults(fn=cmd_list)

    q = sub.add_parser("update", help="按 ID 改字段")
    q.add_argument("xlsx")
    q.add_argument("id")
    q.add_argument("--status", choices=STATUSES)
    q.add_argument("--owner", choices=OWNERS)
    q.add_argument("--severity", choices=SEV)
    q.add_argument("--action")
    q.add_argument("--decision")
    q.add_argument("--desc")
    q.add_argument("--title")
    q.set_defaults(fn=cmd_update)

    q = sub.add_parser("close", help="关闭一行（需决策 ID）")
    q.add_argument("xlsx")
    q.add_argument("id")
    q.add_argument("--decision", required=True)
    q.set_defaults(fn=cmd_close)

    q = sub.add_parser("export", help="导出 CSV")
    q.add_argument("xlsx")
    q.add_argument("--out")
    q.set_defaults(fn=cmd_export)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
