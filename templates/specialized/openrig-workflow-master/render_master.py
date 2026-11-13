#!/usr/bin/env python3
"""Render one self-contained OpenRig execution bundle from the hybrid master.

This script is intentionally side-effect-free: it only writes the generated
OpenRig rig/workflow/AgentSpec/guidance/bridge files. It never starts a daemon,
launches a rig, sends a model prompt, or modifies the checked project.

Exit codes:
  0  bundle rendered (or --dry-run plan printed)
  2  invalid arguments (stderr names the offending field)
  3  render failure (unrendered placeholder, missing template or VERSION)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent
TPL_DIR = TEMPLATE_DIR / "templates"
VERSION_FILE = TEMPLATE_DIR / "VERSION"
MANIFEST_NAME = "render-manifest.json"
BRIDGE_NAME = "OPENRIG-BRIDGE.json"

# Declarative render table: destination (relative to bundle root) -> template.
# Adding an artifact is a one-line change here; there is no per-file write code.
ARTIFACTS: tuple[tuple[str, str], ...] = (
    ("rig.yaml", "rig.yaml.tpl"),
    ("workflow.yaml", "workflow.yaml.tpl"),
    ("agents/worker/agent.yaml", "agent.yaml.tpl"),
    ("guidance/team.md", "guidance-team.md"),
)
# Files shipped in the manifest: the four templates above plus the bridge.
MANIFEST_FILES = tuple(dest for dest, _ in ARTIFACTS) + (BRIDGE_NAME,)

RUN_ID_RE = re.compile(r"[a-z0-9][a-z0-9-]*")
PLACEHOLDER_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")


class RenderError(Exception):
    """A render failed for a reason that is not an argument error."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exit codes: 0 ok, 2 invalid arguments, 3 render failure.\n"
            "--dry-run prints the plan and the artifact hashes without writing anything.\n"
            "--json prints one machine-readable report on stdout (errors still go to stderr)."
        ),
    )
    p.add_argument("--run-id", required=True, help="workflow-group run id, lower-kebab-case")
    p.add_argument("--project-root", default=os.getcwd(), help="project the rig will work on")
    p.add_argument("--output-dir", default=None, help="generated bundle dir (default: runs/<run-id>/openrig)")
    p.add_argument("--rig-name", default=None, help="unique OpenRig rig name (default: openrig-<run-id>)")
    p.add_argument("--workflow-id", default=None, help="unique workflow id (default: openrig-workflow-<run-id>)")
    p.add_argument("--openrig-cli", default="rig", help="rig CLI executable or wrapper")
    p.add_argument("--openrig-home", default=None, help="isolated OPENRIG_HOME (default: /tmp/openrig-workflow-<run-id>)")
    p.add_argument("--daemon-port", type=int, default=47890, help="isolated daemon port (1-65535)")
    p.add_argument("--opencode-model", default="opencode-go/deepseek-v4.1-flash")
    p.add_argument("--dsh-profile", default="headless")
    p.add_argument("--opencode-bin", default="opencode")
    p.add_argument("--dsh-bin", default="dsh")
    p.add_argument("--template-dir", default=None, help="override the template directory (default: ./templates)")
    p.add_argument("--dry-run", action="store_true", help="validate and render in memory; write nothing")
    p.add_argument("--json", action="store_true", help="emit a machine-readable report on stdout")
    p.add_argument("--force", action="store_true", help="overwrite an existing generated bundle")
    args = p.parse_args(argv)

    validate_args(args, p)
    return args


def validate_args(args: argparse.Namespace, p: argparse.ArgumentParser) -> None:
    """Fail before any write, naming the offending field on stderr (exit 2)."""
    if not RUN_ID_RE.fullmatch(args.run_id or ""):
        p.error(f"--run-id must be lower-kebab-case {RUN_ID_RE.pattern} (got {args.run_id!r})")

    project_root = str(Path(args.project_root).expanduser())
    if not Path(project_root).is_dir():
        p.error(f"--project-root is not a directory: {project_root}")

    if not 1 <= args.daemon_port <= 65535:
        p.error(f"--daemon-port must be within 1..65535 (got {args.daemon_port})")

    if args.output_dir is not None and not args.output_dir.strip():
        p.error("--output-dir must be non-empty when given (omit it to use runs/<run-id>/openrig)")

    if args.template_dir is not None and not Path(args.template_dir).expanduser().is_dir():
        p.error(f"--template-dir is not a directory: {args.template_dir}")

    output = Path(args.output_dir or f"runs/{args.run_id}/openrig").expanduser()
    if output.exists():
        if not output.is_dir():
            p.error(f"--output-dir exists and is not a directory: {output}")
        if any(output.iterdir()) and not args.force:
            p.error(f"--output-dir is not empty: {output} (add --force to overwrite the generated bundle)")


def yaml_scalar(value: str) -> str:
    # JSON string literals are valid YAML double-quoted scalars and handle
    # spaces, unicode, and most punctuation safely.
    return json.dumps(value, ensure_ascii=False)


def render(template: str, values: dict[str, str]) -> str:
    out = template
    for key, value in values.items():
        out = out.replace("{{" + key + "}}", value)
    left = PLACEHOLDER_RE.findall(out)
    if left:
        raise RenderError(f"unrendered placeholders: {sorted(set(left))}")
    return out


def master_version() -> str:
    if not VERSION_FILE.is_file():
        raise RenderError(f"master VERSION file not found: {VERSION_FILE}")
    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    if not version:
        raise RenderError(f"master VERSION file is empty: {VERSION_FILE}")
    return version


def rendered_at() -> str:
    """UTC ISO-8601 stamp for the manifest; never part of an artifact sha256."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_template(tpl_dir: Path, name: str) -> str:
    path = tpl_dir / name
    if not path.is_file():
        raise RenderError(f"template not found: {path}")
    return path.read_text(encoding="utf-8")


def build_bridge(args: argparse.Namespace, output: Path, rig_name: str, workflow_id: str, project_root: str) -> dict:
    # schemaVersion 2 (G1/D-002): the bundle describes itself with paths relative to
    # the bundle directory, so the whole directory can be copied/moved without a
    # rewrite and two renders with identical inputs stay byte-identical. Only the
    # runtime fields (projectRoot/openrigHome/openrigCli) keep absolute,
    # machine-local semantics; `output` is intentionally unused here.
    openrig_home = args.openrig_home or f"/tmp/openrig-workflow-{args.run_id}"
    return {
        "schemaVersion": 2,
        "runId": args.run_id,
        "projectRoot": project_root,
        "bundleDir": ".",
        "rigName": rig_name,
        "workflowId": workflow_id,
        "rigSpec": "rig.yaml",
        "workflowSpec": "workflow.yaml",
        "openrigCli": args.openrig_cli,
        "openrigHome": openrig_home,
        "daemonPort": args.daemon_port,
        "seatMap": {
            "main": f"control-main@{rig_name}",
            "pmo": f"control-pmo@{rig_name}",
            "tdo_opencode": f"exec-tdo-oc@{rig_name}",
            "tdo_dsh": f"exec-tdo-dsh@{rig_name}",
            "qa": f"assurance-qa@{rig_name}",
        },
        "runtimeEnv": {
            "OPENRIG_OPENCODE_BIN": args.opencode_bin,
            "OPENRIG_DSH_BIN": args.dsh_bin,
            "OPENRIG_OPENCODE_MODEL": args.opencode_model,
            "OPENRIG_DSH_PROFILE": args.dsh_profile,
        },
        "policy": {
            "mode": "managed-isolated",
            "maxActiveAgents": 2,
            "maxHops": 10,
            "preferResume": True,
            "safetyMode": "on-demand",
            "allowSourceChanges": True,
        },
    }


def artifacts_in_memory(
    args: argparse.Namespace, tpl_dir: Path, output: Path, bridge: dict
) -> dict[str, bytes]:
    """Render every artifact (and the bridge) without touching the filesystem."""
    rig_name = bridge["rigName"]
    workflow_id = bridge["workflowId"]
    project_root = bridge["projectRoot"]
    values = {
        "RUN_ID": args.run_id,
        "PROJECT_ROOT": project_root,
        "PROJECT_ROOT_YAML": yaml_scalar(project_root),
        "RIG_NAME": yaml_scalar(rig_name),
        "RIG_NAME_RAW": rig_name,
        "WORKFLOW_ID": yaml_scalar(workflow_id),
        "WORKFLOW_ID_RAW": workflow_id,
        "OPENCODE_MODEL_YAML": yaml_scalar(args.opencode_model),
        "OPENCODE_MODEL_RAW": args.opencode_model,
        "DSH_PROFILE_RAW": args.dsh_profile,
    }
    files: dict[str, bytes] = {}
    for dest, template_name in ARTIFACTS:
        text = render(load_template(tpl_dir, template_name), values)
        files[dest] = text.encode("utf-8")
    files[BRIDGE_NAME] = (json.dumps(bridge, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    return files


def file_records(files: dict[str, bytes]) -> list[dict]:
    templates = dict(ARTIFACTS)
    records = []
    for dest in MANIFEST_FILES:
        data = files[dest]
        records.append(
            {
                "path": dest,
                "template": templates.get(dest),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    return records


def template_hashes(tpl_dir: Path) -> dict[str, str]:
    """sha256 of every template read for this render (plan I-3: templates counted)."""
    return {
        name: hashlib.sha256(load_template(tpl_dir, name).encode("utf-8")).hexdigest()
        for _, name in ARTIFACTS
    }


def build_manifest(
    master: str, args: argparse.Namespace, records: list[dict], tpl_hashes: dict[str, str], stamp: str
) -> dict:
    # Paths stay relative so the manifest is comparable across output dirs.
    # renderedAt is metadata only and is never covered by an artifact sha256.
    return {
        "schemaVersion": 1,
        "masterVersion": master,
        "renderedAt": stamp,
        "runId": args.run_id,
        "rigName": args.rig_name or f"openrig-{args.run_id}",
        "workflowId": args.workflow_id or f"openrig-workflow-{args.run_id}",
        "daemonPort": args.daemon_port,
        "files": {
            record["path"]: {
                "template": record["template"],
                "bytes": record["bytes"],
                "sha256": record["sha256"],
            }
            for record in records
        },
        "templates": tpl_hashes,
    }


def next_commands(args: argparse.Namespace, output: Path, bridge: dict) -> list[str]:
    q = shlex.quote
    commands = [f"export {key}={q(value)}" for key, value in bridge["runtimeEnv"].items()]
    commands.insert(0, f"export OPENRIG_HOME={q(bridge['openrigHome'])}")
    commands.append(f"{q(args.openrig_cli)} daemon start --no-kernel --port {args.daemon_port}")
    commands.append(
        f"{q(args.openrig_cli)} up {q(str(output / 'rig.yaml'))} "
        f"--cwd {q(bridge['projectRoot'])} --non-interruptive --yes --json"
    )
    commands.append(f"{q(args.openrig_cli)} workflow validate {q(str(output / 'workflow.yaml'))} --json")
    commands.append(
        f"{q(args.openrig_cli)} workflow instantiate {q(str(output / 'workflow.yaml'))} "
        f"--root-objective {q('Execute run ' + args.run_id)} "
        f"--created-by {q('control-main@' + bridge['rigName'])} --json"
    )
    return commands


def report_json(
    args: argparse.Namespace,
    output: Path,
    master: str,
    records: list[dict],
    commands: list[str],
    manifest: dict,
) -> dict:
    return {
        "ok": True,
        "dryRun": bool(args.dry_run),
        "schemaVersion": manifest["schemaVersion"],
        "masterVersion": master,
        "renderedAt": manifest["renderedAt"],
        "runId": args.run_id,
        "rigName": manifest["rigName"],
        "workflowId": manifest["workflowId"],
        "daemonPort": args.daemon_port,
        "outputDir": str(output),
        "manifest": str(output / MANIFEST_NAME),
        "files": records,
        # Plan I-1 names this key "next"; "nextCommands" is kept for callers
        # written against the earlier draft.
        "next": commands,
        "nextCommands": commands,
    }


def print_human(report: dict, output: Path) -> None:
    # Non-dry-run stdout stays byte-compatible with v1.0.0; a dry run says so
    # instead of claiming a write that did not happen.
    print(f"{'would render' if report['dryRun'] else 'rendered'}: {output}")
    print("next:")
    for command in report["nextCommands"]:
        print(f"  {command}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    tpl_dir = Path(args.template_dir).expanduser().resolve() if args.template_dir else TPL_DIR
    project_root = str(Path(args.project_root).expanduser().resolve())
    output = Path(args.output_dir or f"runs/{args.run_id}/openrig").expanduser().resolve()

    try:
        master = master_version()
        rig_name = args.rig_name or f"openrig-{args.run_id}"
        workflow_id = args.workflow_id or f"openrig-workflow-{args.run_id}"
        bridge = build_bridge(args, output, rig_name, workflow_id, project_root)
        files = artifacts_in_memory(args, tpl_dir, output, bridge)
        records = file_records(files)
        manifest = build_manifest(master, args, records, template_hashes(tpl_dir), rendered_at())
    except RenderError as exc:
        print(f"render failed: {exc}", file=sys.stderr)
        return 3

    referenced = {name for _, name in ARTIFACTS}
    for leftover in sorted(p.name for p in tpl_dir.iterdir() if p.is_file()):
        if leftover.endswith((".tpl", ".md")) and leftover not in referenced:
            print(f"warning: template not referenced by ARTIFACTS: {leftover}", file=sys.stderr)

    commands = next_commands(args, output, bridge)
    report = report_json(args, output, master, records, commands, manifest)

    if args.dry_run:
        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print_human(report, output)
        return 0

    for dest, data in files.items():
        target = output / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    (output / MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_human(report, output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
