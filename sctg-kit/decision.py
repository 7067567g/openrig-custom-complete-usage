# Copyright 2026 SCTG contributors
# Licensed under the Apache License, Version 2.0.
"""Decision Channel v0：让「批准」成为一个可校验的对象，而不是一句话。

一条 Decision 要成立，必须同时满足：

1. 至少两个选项（`OPTIONS_MIN`）——只有一个选项的"决策"是通知；
2. 有明确 scope（`SCOPE_MISSING`）——不写清约束什么，等于没约束；
3. 有未过期的 expiry（`EXPIRY_*`）——永久授权是最容易被遗忘的漏洞；
4. 批准人不是请求人、也不是被批对象的产出者（`SELF_REVIEW`）——自审不是审批；
5. 绑定被批对象的内容 hash（`BINDING_MISSING`）——否则"批的是哪一版"无法回答；
6. 若是模式变更，必须有 `from/to/rollback`（`MODE_FIELDS`）且转换合法（`MODE_TRANSITION`）。

聊天、评论、`rig send` 都不产生 Decision：它们没有 id、没有 hash、没有 expiry。
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

MODES = ("shadow", "lite", "full")
DECISIONS = ("approved", "rejected")
# 允许的升级路径：不允许 Shadow 直跳 Full
TRANSITIONS: dict[tuple[str, str], dict[str, Any]] = {
    ("shadow", "lite"): {"requires": ["rollback", "decision"], "note": "需 Decision + 回滚方案；Lite 至少 1 个 run"},
    ("lite", "full"): {"requires": ["rollback", "decision", "lite_run_evidence"], "note": "需独立 Decision + 回滚 + Lite 实跑证据"},
    ("shadow", "full"): {"requires": [], "forbidden": True, "note": "禁止由 Shadow 直跳 Full"},
    ("lite", "shadow"): {"requires": ["rollback"], "note": "降级同样要留痕"},
    ("full", "lite"): {"requires": ["rollback"], "note": "降级同样要留痕"},
}


def load(path: Path) -> dict:
    import yaml

    text = Path(path).read_text(encoding="utf-8")
    if str(path).endswith(".json"):
        import json

        return json.loads(text)
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"decision doc must be a mapping: {path}")
    return data


def _ts(value) -> dt.datetime | None:
    try:
        parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)


def validate_request(req: dict[str, Any], *, now: str) -> list[dict[str, Any]]:
    errors: list[dict] = []

    def err(code: str, detail: str) -> None:
        errors.append({"code": code, "detail": detail})

    for field in ("id", "requested_by", "subject", "object_hash", "recommendation", "conditions", "expiry"):
        if req.get(field) in (None, "", [], {}):
            err("REQ_FIELD", f"missing/empty: {field}")
    if errors:
        return errors

    options = req.get("options") or []
    if not isinstance(options, list) or len(options) < 2:
        err("OPTIONS_MIN", f"{req['id']}: needs >=2 options, got {options!r}")
    if options and req.get("recommendation") not in [o.get("id") for o in options if isinstance(o, dict)]:
        err("RECOMMENDATION", f"{req['id']}: recommendation must be one of the option ids")

    if not isinstance(req.get("scope"), list) or not req.get("scope"):
        err("SCOPE_MISSING", f"{req['id']}: scope must be a non-empty list")

    if not str(req["object_hash"]).startswith("sha256:"):
        err("BINDING_MISSING", f"{req['id']}: object_hash must bind the reviewed version")

    expiry = _ts(req["expiry"])
    now_ts = _ts(now) or dt.datetime.now(dt.timezone.utc)
    if expiry is None:
        err("EXPIRY_INVALID", f"{req['id']}: expiry must be an ISO timestamp")
    elif expiry < now_ts:
        err("EXPIRY_PAST", f"{req['id']}: expiry {req['expiry']} already passed")

    mode = req.get("mode_change")
    if mode is not None:
        for field in ("from_mode", "to_mode", "rollback"):
            if not mode.get(field):
                err("MODE_FIELDS", f"{req['id']}: mode_change missing {field}")
        if mode.get("from_mode") and mode.get("to_mode"):
            trans = TRANSITIONS.get((mode["from_mode"], mode["to_mode"]))
            if trans is None:
                err("MODE_TRANSITION", f"{req['id']}: {mode['from_mode']}→{mode['to_mode']} not allowed")
            elif trans.get("forbidden"):
                err("MODE_TRANSITION", f"{req['id']}: {trans['note']}")

    return errors


def decide(req: dict[str, Any], *, approver: str, choice: str, now: str, producer: str | None = None) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """MAIN 落 Decision Record。自审、越界选择、过期都在这里被挡。"""
    errors = validate_request(req, now=now)
    if errors:
        return None, errors

    if approver != "MAIN":
        return None, [{"code": "APPROVER_NOT_MAIN", "detail": f"approver={approver!r}; MAIN 是唯一审批者"}]
    if approver == req.get("requested_by"):
        return None, [{"code": "SELF_REVIEW", "detail": "approver cannot be the requester"}]
    if producer and approver == producer:
        return None, [{"code": "SELF_REVIEW", "detail": "approver cannot be the producer of the object"}]

    option_ids = [o.get("id") for o in req["options"]]
    if choice not in option_ids:
        return None, [{"code": "CHOICE_INVALID", "detail": f"choice={choice!r} not in {option_ids}"}]

    record: dict[str, Any] = {
        "schema": "sctg/decision-record/v1",
        "decision_id": f"D-{req['id']}",
        "request_id": req["id"],
        "approved_by": approver,
        "decision": "approved",
        "chosen_option": choice,
        "subject": req["subject"],
        "scope": list(req["scope"]),
        "conditions": req["conditions"],
        "expiry": req["expiry"],
        "bound_object_hash": req["object_hash"],
        "mode_change": req.get("mode_change"),
        "at": now,
    }
    if record["mode_change"]:
        trans = TRANSITIONS.get((record["mode_change"]["from_mode"], record["mode_change"]["to_mode"]), {})
        record["required_evidence"] = trans.get("requires", [])
    return record, []


def is_authorized(record: dict[str, Any], *, now: str, action_scope: str) -> tuple[bool, str]:
    """一条 Decision 能不能授权某个动作：要过状态、过期、scope 覆盖三关。"""
    if record.get("decision") != "approved":
        return False, "NOT_APPROVED"
    expiry = _ts(record.get("expiry"))
    now_ts = _ts(now) or dt.datetime.now(dt.timezone.utc)
    if expiry is None:
        return False, "EXPIRY_INVALID"
    if expiry < now_ts:
        return False, "EXPIRED"
    scope = record.get("scope") or []
    for item in scope:
        if item == "*" or item == action_scope:
            return True, "OK"
        if item.endswith("/**") and action_scope.startswith(item[:-3].rstrip("/") + "/"):
            return True, "OK"
    return False, "SCOPE_NOT_COVERED"


def mode_policy() -> dict[str, Any]:
    """三种模式的门槛与回滚要求，写死在代码里，避免口头约定。"""
    return {
        "schema": "sctg/mode-policy/v1",
        "current_default": "shadow",
        "modes": {
            "shadow": {
                "description": "旁路记录；不改变主流程写权",
                "entry_requires": [],
                "exit_to_lite": ["Decision（含 rollback）", "至少 1 个 Lite pilot run 计划"],
                "human_in_loop": False,
            },
            "lite": {
                "description": "SCTG 参与推进，但保留人工/宿主兜底",
                "entry_requires": ["Decision", "rollback", "scope/expiry"],
                "exit_to_full": ["独立 Decision", "rollback", "Lite 实跑证据（≥1 run）"],
                "human_in_loop": False,
            },
            "full": {
                "description": "SCTG 驱动主流程；代价与风险最高",
                "entry_requires": ["独立 Decision", "rollback", "Lite 实跑证据", "成本可采集或显式 unavailable"],
                "human_in_loop": False,
            },
        },
        "transitions": {
            f"{a}->{b}": {k: v for k, v in spec.items()} for (a, b), spec in TRANSITIONS.items()
        },
        "rollback_required_on": ["shadow->lite", "lite->full", "lite->shadow", "full->lite"],
    }


def validate_record(record: dict[str, Any], *, now: str) -> list[dict[str, Any]]:
    errors: list[dict] = []

    def err(code: str, detail: str) -> None:
        errors.append({"code": code, "detail": detail})

    for field in ("decision_id", "request_id", "approved_by", "decision", "chosen_option", "scope", "conditions", "expiry", "bound_object_hash"):
        if record.get(field) in (None, "", [], {}):
            err("REC_FIELD", f"missing/empty: {field}")
    if record.get("approved_by") != "MAIN":
        err("REC_APPROVER", f"approved_by={record.get('approved_by')!r}")
    if record.get("decision") not in DECISIONS:
        err("REC_DECISION", f"decision={record.get('decision')!r}")
    expiry = _ts(record.get("expiry"))
    if expiry is None:
        err("REC_EXPIRY", "expiry unparseable")
    return errors
