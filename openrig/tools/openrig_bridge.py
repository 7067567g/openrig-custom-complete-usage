#!/usr/bin/env python3
"""Small operational bridge for an OpenRig hybrid-master run.

Commands are deliberately read-only except for writing status/evidence files:

  status  -> OPENRIG-STATE.json + human summary
  capture -> copy/inspect transcripts + capture-manifest.json
  doctor  -> cross-check bridge/CLI/spec/home wiring

Exit codes:

  status   0 all seats ready and every source collected; 2 degraded
  capture  0 captured+clean; 3 secret-pattern hit; 1 source/CLI failure
  doctor   0 PASS; 1 FAIL (one ``FAIL <field> bridge=... spec=...`` line each)

It never mutates queue/workflow state and never starts/stops a daemon.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 2
# Bridge carrier schema versions `doctor` understands (G1/D-002/D-007):
#   v1 = legacy bundle that stored absolute paths; still read-only compatible
#   v2 = bundle that stores paths relative to the bundle and never escapes it
LEGACY_BRIDGE_SCHEMA = 1
BRIDGE_SCHEMA_VERSION = 2
SUPPORTED_BRIDGE_SCHEMAS = (LEGACY_BRIDGE_SCHEMA, BRIDGE_SCHEMA_VERSION)
TAIL_LINES = 50_000
# Keep the patterns narrow enough to avoid prose false positives ("task-" is not a key).
SECRET_PATTERNS = (
    ("openai-sk", re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{8,}")),
    ("openai-env", re.compile(r"OPENAI_API_KEY\s*=")),
    ("bearer", re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]{8,}")),
)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_bridge(run_dir: Path) -> dict:
    p = run_dir / "openrig" / "OPENRIG-BRIDGE.json"
    if not p.is_file():
        raise SystemExit(f"bridge not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def cli_args(bridge: dict) -> list[str]:
    raw = bridge.get("openrigCli") or "rig"
    return shlex.split(raw)


def run_cli(bridge: dict, args: list[str], timeout: int = 60) -> subprocess.CompletedProcess[str]:
    """Run the bridge CLI; never raise for the two operational failures we report."""
    cmd = [*cli_args(bridge), *args]
    try:
        return subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
    except FileNotFoundError as exc:
        return subprocess.CompletedProcess(cmd, 127, "", f"CLI not found: {exc}")
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        return subprocess.CompletedProcess(cmd, 124, stdout, f"timeout after {timeout}s")
    except OSError as exc:
        return subprocess.CompletedProcess(cmd, 126, "", f"could not run CLI: {exc}")


def _try_json(text: str):
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


# --------------------------------------------------------------------------- status


def _pick_instance(bridge: dict) -> tuple[dict | None, subprocess.CompletedProcess[str], list]:
    """Return the active instance for this run's workflow id (latest if several)."""
    proc = run_cli(bridge, ["workflow", "list", "--json"])
    data = _try_json(proc.stdout)
    instances = data if isinstance(data, list) else []
    wanted = bridge.get("workflowId")
    candidates = [i for i in instances if isinstance(i, dict) and i.get("workflowName") == wanted]
    active = [i for i in candidates if i.get("status") == "active"]
    pool = active or candidates
    if not pool:
        return None, proc, instances
    return max(pool, key=lambda i: i.get("createdAt") or ""), proc, instances


def _frontier(instance: dict | None) -> dict:
    if not instance:
        return {"instance": None, "status": None, "step": None, "owner": None, "frontier": []}
    packets = [p for p in instance.get("frontierPackets") or [] if isinstance(p, dict)]
    rows = [
        {
            "packetId": p.get("packetId"),
            "step": p.get("stepId"),
            "owner": p.get("ownerSession"),
            "queueState": p.get("queueState"),
        }
        for p in packets
    ]
    steps = [r["step"] for r in rows if r["step"]] or ([instance.get("currentStepId")] if instance.get("currentStepId") else [])
    owners = sorted({r["owner"] for r in rows if r["owner"]})
    return {
        "instance": instance.get("instanceId"),
        "workflow": instance.get("workflowName"),
        "status": instance.get("status"),
        "step": ",".join(steps) if steps else None,
        "owner": ",".join(owners) if owners else None,
        "frontier": rows,
    }


def cmd_status(run_dir: Path, as_json: bool) -> int:
    bridge = load_bridge(run_dir)
    rig = bridge["rigName"]
    generated = now_iso()
    errors: list[str] = []
    sources: dict[str, dict] = {}

    ps = run_cli(bridge, ["ps", "--nodes", "--rig", rig, "--full", "--json"])
    nodes_raw = _try_json(ps.stdout)
    nodes = nodes_raw if isinstance(nodes_raw, list) else []
    seats = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        seats.append(
            {
                "role": node.get("role"),
                "session": node.get("canonicalSessionName"),
                "startupStatus": node.get("startupStatus"),
                "sessionStatus": node.get("sessionStatus"),
            }
        )
    ready = sum(1 for s in seats if s["startupStatus"] == "ready")
    sources["rigPs"] = {"rc": ps.returncode, "ok": ps.returncode == 0 and isinstance(nodes_raw, list)}
    if not sources["rigPs"]["ok"]:
        errors.append(f"rig ps failed rc={ps.returncode}: {ps.stderr.strip()[:400]}")

    instance, wf_proc, instances = _pick_instance(bridge)
    frontier = _frontier(instance)
    sources["workflow"] = {
        "rc": wf_proc.returncode,
        "ok": wf_proc.returncode == 0 and isinstance(instances, list),
        "instanceFound": instance is not None,
    }
    if not sources["workflow"]["ok"]:
        errors.append(f"workflow list failed rc={wf_proc.returncode}: {wf_proc.stderr.strip()[:400]}")
    elif instance is None:
        errors.append(f"workflow: no instance for {bridge.get('workflowId')}")

    q = run_cli(bridge, ["queue", "list", "--all-rigs", "--limit", "500", "--json"])
    queue_raw = _try_json(q.stdout)
    queue_items = queue_raw if isinstance(queue_raw, list) else []
    mine = [
        i
        for i in queue_items
        if isinstance(i, dict) and str(i.get("destinationSession", "")).endswith("@" + rig)
    ]
    counts = {"pending": 0, "in-progress": 0, "blocked": 0}
    for item in mine:
        state = str(item.get("state", ""))
        if state in counts:
            counts[state] += 1
    sources["queue"] = {"rc": q.returncode, "ok": q.returncode == 0 and isinstance(queue_raw, list)}
    if not sources["queue"]["ok"]:
        errors.append(f"queue list failed rc={q.returncode}: {q.stderr.strip()[:400]}")

    if not seats:
        errors.append("rig ps returned no seats")
    degraded = bool(errors) or ready != len(seats) or len(seats) == 0

    state = {
        "schemaVersion": SCHEMA_VERSION,
        "runId": bridge.get("runId"),
        "rigName": rig,
        "generatedAt": generated,
        "degraded": degraded,
        "seats": {"total": len(seats), "ready": ready, "nodes": seats},
        "workflow": frontier,
        "queue": {"total": len(mine), **counts},
        "sources": sources,
        "errors": errors,
    }
    out = run_dir / "OPENRIG-STATE.json"
    out.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if as_json:
        print(json.dumps(state, indent=2, ensure_ascii=False))
    else:
        print(f"wrote {out}")
        print(
            f"rig={rig} seats={ready}/{len(seats)} "
            f"workflow={frontier['instance'] or '-'} step={frontier['step'] or '-'} "
            f"owner={frontier['owner'] or '-'} "
            f"queue pending={counts['pending']} in-progress={counts['in-progress']} "
            f"blocked={counts['blocked']} generatedAt={generated}"
        )
        for err in errors:
            print(f"WARN {err}", file=sys.stderr)
    return 2 if degraded else 0


# -------------------------------------------------------------------------- capture


def _copy_transcripts(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst, dirs_exist_ok=True)


def _capture_via_cli(bridge: dict, dst: Path) -> list[str]:
    """Fallback for sandboxed seats that cannot read $OPENRIG_HOME/transcripts."""
    problems: list[str] = []
    for role, seat in (bridge.get("seatMap") or {}).items():
        proc = run_cli(bridge, ["transcript", str(seat), "--tail", str(TAIL_LINES), "--json"], timeout=90)
        data = _try_json(proc.stdout)
        content = data.get("content") if isinstance(data, dict) else None
        if not isinstance(content, str) or not content:
            problems.append(f"{role} ({seat}): transcript rc={proc.returncode} {proc.stderr.strip()[:160]}")
            continue
        (dst / f"{seat}.log").write_text(content, encoding="utf-8")
    return problems


def _scan_secrets(root: Path, files: list[Path]) -> list[dict]:
    hits: list[dict] = []
    for path in files:
        if path.name == "capture-manifest.json":
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for kind, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    hits.append({"file": str(path.relative_to(root)), "line": lineno, "kind": kind})
                    break
    return hits


def cmd_capture(run_dir: Path, source: str | None, out: str | None) -> int:
    bridge = load_bridge(run_dir)
    rig = bridge["rigName"]
    generated = now_iso()
    dst = Path(out).expanduser().resolve() if out else run_dir / "evidence" / "openrig-transcripts" / rig
    src = Path(source).expanduser().resolve() if source else (Path(bridge["openrigHome"]).expanduser() / "transcripts" / rig)
    if src.is_dir() and src.resolve() == dst:
        print(f"capture: source and output are the same directory: {dst}", file=sys.stderr)
        return 1
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)

    manifest: dict = {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": generated,
        "rigName": rig,
        "source": {},
        "files": [],
        "scan": {"patterns": ["sk-<token>", "OPENAI_API_KEY=", "Bearer <token>"], "hits": [], "ok": True},
        "ok": False,
        "errors": [],
    }

    if src.is_dir():
        manifest["source"] = {"kind": "transcripts-dir", "dir": str(src)}
        _copy_transcripts(src, dst)
    else:
        # A sandboxed agent may not see the daemon home; the transcript routes are still live.
        manifest["source"] = {"kind": "cli-fallback", "dir": str(src), "reason": "transcripts dir not readable"}
        manifest["errors"].extend(_capture_via_cli(bridge, dst))

    files = sorted(p for p in dst.rglob("*") if p.is_file() and p.name != "capture-manifest.json")
    manifest["files"] = [
        {"path": str(p.relative_to(dst)), "bytes": p.stat().st_size, "sha256": _sha256(p)} for p in files
    ]
    hits = _scan_secrets(dst, files)
    manifest["scan"] = {"patterns": manifest["scan"]["patterns"], "hits": hits, "ok": not hits}

    if hits:
        rc = 3
        manifest["errors"].append(f"{len(hits)} secret-pattern hit(s); no values were printed")
    elif not files:
        rc = 1
        manifest["errors"].append("no transcript files captured")
    elif manifest["errors"]:
        rc = 1
        manifest["errors"].append("capture was partial; see per-seat errors above")
    else:
        manifest["ok"] = True
        rc = 0

    (dst / "capture-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote {dst / 'capture-manifest.json'} ({len(files)} files, {sum(f['bytes'] for f in manifest['files'])} bytes)")
    for err in manifest["errors"]:
        print(f"WARN {err}", file=sys.stderr)
    for hit in hits:
        print(f"FAIL secret pattern {hit['kind']} in {hit['file']}:{hit['line']}", file=sys.stderr)
    return rc


# --------------------------------------------------------------------------- doctor


def _looks_like_path(token: str) -> bool:
    """True when an argv token is meant as a filesystem path rather than a flag/word.

    `openrigCli` may be a multi-word command (``node /abs/bin-wrapper.js``); only the
    path-shaped tokens are checked, so flags such as ``--port`` are never reported.
    """
    if "/" in token or "\\" in token:
        return True
    if token.startswith(("~", ".")):
        return True
    return token.endswith((".js", ".mjs", ".cjs", ".py", ".ts", ".sh", ".exe", ".cmd", ".bat"))


def _missing_cli_parts(raw: str) -> list[tuple[int, str]]:
    """Every unresolvable path-type argv element of `openrigCli`, in argv order.

    Checking only ``argv[0]`` was the A-2 false PASS: ``node /missing/wrapper.js``
    passed because ``node`` exists even though the script it runs does not.
    """
    try:
        parts = shlex.split(raw)
    except ValueError as exc:  # unbalanced quotes: unparseable is a failure, not a skip
        return [(0, f"<unparseable openrigCli: {exc}>")]
    missing: list[tuple[int, str]] = []
    for index, token in enumerate(parts):
        if index != 0 and not _looks_like_path(token):
            continue
        candidate = Path(token).expanduser()
        if not (candidate.exists() or shutil.which(token)):
            missing.append((index, token))
    return missing


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except (ValueError, OSError):
        return False
    return True


def _looks_absolute(value: str) -> bool:
    """True when a bridge path is absolute (POSIX root or Windows drive/UNC).

    schemaVersion=2 requires bundle-relative paths, so any absolute value is a
    contract failure rather than a resolvable path.
    """
    if value.startswith(("/", "\\\\")):
        return True
    return bool(re.match(r"^[A-Za-z]:[\\/]", value))


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value


def _fallback_yaml(text: str) -> dict:
    """Tiny reader for the generated master specs, used only when PyYAML is absent.

    It intentionally understands just the fields doctor compares; anything it cannot
    read stays absent and therefore surfaces as a FAIL rather than a false PASS.
    """
    rig: dict = {"name": None, "members": []}
    workflow: dict = {"id": None, "rig": None, "roles": {}}
    section = None
    role = None
    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if indent == 0 and stripped.endswith(":"):
            section = stripped[:-1]
            continue
        if stripped.startswith("- id:"):
            rig["members"].append({"id": _unquote(stripped.split(":", 1)[1])})
            continue
        if section == "workflow" or stripped.startswith("id:"):
            if indent <= 2 and stripped.startswith("id:") and workflow["id"] is None:
                workflow["id"] = _unquote(stripped.split(":", 1)[1])
                continue
        if stripped.startswith("name:") and indent == 0:
            rig["name"] = _unquote(stripped.split(":", 1)[1])
            continue
        if indent == 0 and stripped.startswith("version:"):
            continue
        if section == "target" and stripped.startswith("rig:"):
            workflow["rig"] = _unquote(stripped.split(":", 1)[1])
            continue
        if stripped == "target:" or stripped == "roles:" or stripped == "members:":
            section = stripped[:-1]
            continue
        if indent == 4 and stripped.endswith(":") and section == "roles":
            role = stripped[:-1]
            workflow["roles"][role] = {}
            continue
        if role and stripped.startswith("preferred_targets:"):
            raw_list = stripped.split(":", 1)[1].strip().strip("[]")
            workflow["roles"][role]["preferred_targets"] = [
                _unquote(v) for v in raw_list.split(",") if v.strip()
            ]
            continue
        if section == "members" and stripped.startswith(("role:", "cwd:")):
            key, _, value = stripped.partition(":")
            if rig["members"]:
                rig["members"][-1][key.strip()] = _unquote(value)
    return {"name": rig["name"], "pods": [{"members": [m for m in rig["members"] if "cwd" in m and "role" in m]}], "workflow": workflow}


def _load_spec(path: Path, kind: str) -> dict:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
    except ImportError:
        return _fallback_yaml(text)
    loaded = yaml.safe_load(text)
    return loaded if isinstance(loaded, dict) else {}


def _doctor_check(bridge: dict, run_dir: Path) -> tuple[list[str], list[str]]:
    failures: list[str] = []

    def fmt(value) -> str:
        return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)

    def fail(field: str, bridge_value, spec_value) -> None:
        failures.append(f"FAIL {field} bridge={fmt(bridge_value)} spec={fmt(spec_value)}")

    for key in (
        "runId",
        "projectRoot",
        "bundleDir",
        "rigName",
        "workflowId",
        "rigSpec",
        "workflowSpec",
        "openrigHome",
        "seatMap",
    ):
        if not bridge.get(key):
            failures.append(f"FAIL missing bridge field {key}")
    if failures:
        return failures, []

    # D-009/P-002: the bridge carrier has its own contract version and SAFETY mode.
    # v1 (legacy, absolute paths) is read for compatibility; v2 (bundle-relative
    # paths) is what render_master.py now emits. Both carry safetyMode=on-demand.
    bridge_schema = bridge.get("schemaVersion")
    supported = "|".join(str(v) for v in SUPPORTED_BRIDGE_SCHEMAS)
    if isinstance(bridge_schema, bool) or not isinstance(bridge_schema, int) or bridge_schema not in SUPPORTED_BRIDGE_SCHEMAS:
        value = "(missing)" if bridge_schema is None else bridge_schema
        failures.append(f"FAIL schemaVersion bridge={fmt(value)} spec={supported}")
        bridge_schema = None
    policy = bridge.get("policy")
    if not isinstance(policy, dict):
        failures.append("FAIL policy bridge=(missing) spec=object with safetyMode=on-demand|always")
    else:
        safety_mode = policy.get("safetyMode")
        if safety_mode not in ("on-demand", "always"):
            value = "(missing)" if safety_mode is None else safety_mode
            failures.append(f"FAIL policy.safetyMode bridge={fmt(value)} spec=on-demand|always")

    project_root = Path(bridge["projectRoot"])
    if not project_root.is_dir():
        failures.append(f"FAIL projectRoot bridge={str(project_root)!r} spec=missing directory")

    # A-1: the bridge named a run that the run directory did not hold. Doctor loaded the
    # bridge *from* `run_dir`, so `runId` must agree with that directory's name; otherwise
    # a bridge copied/pasted from another run silently "passed".
    run_id = bridge["runId"]
    if run_dir.name != run_id:
        fail("runId", run_id, run_dir.name)

    # A-3 + G1: bundleDir was never read. The bundle is the directory this bridge lives in.
    # v2 additionally requires a *relative* bundleDir (".") that resolves to that
    # directory, so a moved bundle keeps validating.
    expected_bundle = run_dir / "openrig"
    relative_required = bridge_schema == BRIDGE_SCHEMA_VERSION
    bundle_raw = str(bridge["bundleDir"])
    if relative_required and _looks_absolute(bundle_raw):
        fail("bundleDir.relative", bundle_raw, "relative path (schemaVersion=2)")
    bundle = (expected_bundle / bundle_raw) if relative_required else Path(bundle_raw).expanduser()
    if not bundle.is_dir():
        fail("bundleDir", bundle_raw, f"missing directory (expected {expected_bundle})")
        bundle_ok = False
    elif bundle.resolve() != expected_bundle.resolve():
        fail("bundleDir", bundle_raw, str(expected_bundle))
        bundle_ok = False
    else:
        bundle_ok = True

    # A-2: `openrigCli` may be a multi-word command; validate every path-type argv element.
    cli_raw = str(bridge["openrigCli"])
    for index, token in _missing_cli_parts(cli_raw):
        fail("openrigCli", token, f"not found (argv[{index}] of {cli_raw!r})")

    # G1: v2 spec paths must be relative to the bundle and must not escape it; v1 kept
    # absolute paths, which are still resolved as before (read-only compatibility).
    rig_spec_raw = str(bridge["rigSpec"])
    wf_spec_raw = str(bridge["workflowSpec"])
    for raw, label in ((rig_spec_raw, "rig.yaml"), (wf_spec_raw, "workflow.yaml")):
        if relative_required and _looks_absolute(raw):
            fail(f"{label}.relative", raw, "relative path (schemaVersion=2)")
    if relative_required:
        rig_spec = expected_bundle / rig_spec_raw
        wf_spec = expected_bundle / wf_spec_raw
    else:
        rig_spec = Path(rig_spec_raw).expanduser()
        wf_spec = Path(wf_spec_raw).expanduser()
    for path, label in ((rig_spec, "rig.yaml"), (wf_spec, "workflow.yaml")):
        if not path.is_file():
            failures.append(f"FAIL specFile bridge={str(path)!r} spec=missing")
        elif bundle_ok and not _is_within(path, expected_bundle):
            fail(f"{label}.inBundle", str(path), f"outside bundleDir {expected_bundle}")

    notes: list[str] = []
    if bridge_schema == LEGACY_BRIDGE_SCHEMA:
        notes.append(
            "legacy bridge schemaVersion=1 (absolute bundle paths); read-only compatible "
            "- re-render to migrate to schemaVersion=2"
        )
    elif bridge_schema == BRIDGE_SCHEMA_VERSION:
        notes.append("bridge schemaVersion=2 (bundle-relative paths)")
    rig_doc: dict = {}
    wf_doc: dict = {}
    if rig_spec.is_file():
        try:
            rig_doc = _load_spec(rig_spec, "rig")
        except Exception as exc:  # parse error must be a check failure, not a traceback
            failures.append(f"FAIL rigSpec.parse bridge={str(rig_spec)!r} spec={exc}")
        if not rig_doc:
            failures.append(f"FAIL rigSpec.empty bridge={str(rig_spec)!r} spec=no mapping")
    if wf_spec.is_file():
        try:
            wf_doc = _load_spec(wf_spec, "workflow")
        except Exception as exc:
            failures.append(f"FAIL workflowSpec.parse bridge={str(wf_spec)!r} spec={exc}")
        if not wf_doc:
            failures.append(f"FAIL workflowSpec.empty bridge={str(wf_spec)!r} spec=no mapping")

    if rig_doc:
        if rig_doc.get("name") != bridge["rigName"]:
            fail("rigName", bridge["rigName"], rig_doc.get("name"))
        members = []
        for pod in rig_doc.get("pods") or []:
            for member in (pod or {}).get("members") or []:
                if isinstance(member, dict):
                    members.append(member)
        if not members:
            failures.append("FAIL rigSpec.members bridge=seatMap spec=none parsed")
        for member in members:
            cwd = member.get("cwd")
            if cwd is not None and cwd != bridge["projectRoot"]:
                fail(f"member[{member.get('id')}].cwd", bridge["projectRoot"], cwd)

    if wf_doc:
        wf = wf_doc.get("workflow") or {}
        if wf.get("id") != bridge["workflowId"]:
            fail("workflowId", bridge["workflowId"], wf.get("id"))
        target = (wf.get("target") or {}).get("rig")
        if target != bridge["rigName"]:
            fail("workflow.target.rig", bridge["rigName"], target)
        wf_roles = wf.get("roles") or {}
        bridge_roles = bridge["seatMap"]
        for role in sorted(set(bridge_roles) - set(wf_roles)):
            failures.append(f"FAIL roles.{role} bridge=seatMap spec=missing")
        for role in sorted(set(wf_roles) - set(bridge_roles)):
            failures.append(f"FAIL roles.{role} bridge=missing spec=declared")
        for role, seat in bridge_roles.items():
            if seat.split("@")[-1] != bridge["rigName"]:
                fail(f"seatMap[{role}].rig", bridge["rigName"], seat.split("@")[-1])
            targets = (wf_roles.get(role) or {}).get("preferred_targets") or []
            if seat not in targets:
                fail(f"roles[{role}].preferred_targets", seat, targets)

    home = Path(str(bridge["openrigHome"])).expanduser()
    if home.exists():
        if not os.access(home, os.W_OK):
            fail("openrigHome.writable", str(home), "not writable")
        else:
            notes.append(f"home={home} exists writable")
    else:
        parent = home.parent
        if not parent.exists() or not os.access(parent, os.W_OK):
            fail("openrigHome.creatable", str(home), f"parent not writable: {parent}")
        else:
            notes.append(f"home={home} missing but creatable")

    return failures, notes


def cmd_doctor(run_dir: Path) -> int:
    bridge = load_bridge(run_dir)
    try:
        failures, notes = _doctor_check(bridge, run_dir)
    except Exception as exc:  # never lose the partial verdict to a traceback
        failures = [f"FAIL doctor.crashed bridge=- spec={exc}"]
        notes = []
    if failures:
        for line in failures:
            print(line)
        return 1
    print(
        f"PASS bridge runId={bridge['runId']} rig={bridge['rigName']} "
        f"workflow={bridge['workflowId']} schema={bridge.get('schemaVersion')}"
    )
    for note in notes:
        print(f"  {note}")
    print("seat map:")
    for role, seat in bridge["seatMap"].items():
        print(f"  {role:12} {seat}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", choices=["status", "capture", "doctor"])
    p.add_argument("--run-dir", required=True, help="workflow-group run directory")
    p.add_argument("--json", action="store_true", help="status only: print the state object as JSON")
    p.add_argument("--source", help="capture only: transcript directory to copy (default: bridge openrigHome)")
    p.add_argument("--out", help="capture only: output directory (default: run evidence/openrig-transcripts/<rig>)")
    args = p.parse_args()
    run_dir = Path(args.run_dir).expanduser().resolve()
    if args.command == "status":
        return cmd_status(run_dir, args.json)
    if args.command == "capture":
        return cmd_capture(run_dir, args.source, args.out)
    return cmd_doctor(run_dir)


if __name__ == "__main__":
    sys.exit(main())
