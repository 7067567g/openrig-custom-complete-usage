#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OpenRig Lead onboarding guide.

The Lead fills a small set of stage answers. A headless reviewer then checks
those answers against the pinned OpenRig guide content index. The reviewer must
end with an exact verdict string; the guide copies that string, never invents it.

Commands:
  python3 tools/lead-guide/guide.py check-version
  python3 tools/lead-guide/guide.py run [--workdir run] [--answers FILE]
  python3 tools/lead-guide/guide.py review [--workdir run] [--answers FILE]

Version rule: the guide pins the OpenRig guide version and the main-document
hash. If either moves, onboarding is blocked until the guide files are re-pinned.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

GUIDE_DIR = Path(__file__).resolve().parent
REPO_ROOT = GUIDE_DIR.parents[1]
VERSION_PATH = GUIDE_DIR / "version.json"
INDEX_PATH = GUIDE_DIR / "content-index.json"
STAGES_PATH = GUIDE_DIR / "stages.json"
PERSONA_PATH = GUIDE_DIR / "persona" / "LEAD-ONBOARDING.md"
MAIN_DOC_REL = "docs/OPENRIG-WORKFLOW-GUIDE.zh-CN.md"
VERSION_FILE_REL = "VERSION"

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_DRIFT = 3
EXIT_INCOMPLETE = 4
EXIT_SMALL_DEVIATION = 5

VERDICT_PASS = "PASS"
VERDICT_SMALL = "SMALL_DEVIATION"
VERDICT_LARGE = "LARGE_DEVIATION"
VERDICT_INCOMPLETE = "INCOMPLETE"
FINAL_OK = "引导完成"
FINAL_RERUN = "请重新运行引导"
REQUIRED_REVIEW_FIELDS = ("VERDICT", "MISSING", "QUESTIONS", "EXPLANATION", "FINAL")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    try:
        return sha256_bytes(path.read_bytes())
    except FileNotFoundError:
        return ""


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_version(root: Path | None = None, guide_dir: Path | None = None) -> list[str]:
    """Return drift errors. Empty list means the guide is pinned correctly."""
    root = Path(root) if root is not None else REPO_ROOT
    guide_dir = Path(guide_dir) if guide_dir is not None else GUIDE_DIR
    errors: list[str] = []
    version_path = guide_dir / "version.json"
    index_path = guide_dir / "content-index.json"
    if not version_path.is_file():
        return [f"缺少引导版本文件: {version_path}"]
    if not index_path.is_file():
        return [f"缺少内容索引文件: {index_path}"]
    pinned = read_json(version_path)
    version_file = root / VERSION_FILE_REL
    actual_version = version_file.read_text(encoding="utf-8").strip() if version_file.is_file() else None
    actual_doc_hash = sha256_file(root / MAIN_DOC_REL)
    actual_index_hash = sha256_file(index_path)

    if actual_version is None:
        errors.append(f"缺少 OpenRig VERSION 文件: {version_file}")
    elif pinned.get("openrigGuideVersion") != actual_version:
        errors.append(
            f"OpenRig 版本漂移: 引导固定 {pinned.get('openrigGuideVersion')!r}，当前 {actual_version!r}"
        )
    if pinned.get("mainDocSha256") != actual_doc_hash:
        errors.append(
            "主文档哈希漂移: 引导固定的 mainDocSha256 与当前 docs/OPENRIG-WORKFLOW-GUIDE.zh-CN.md 不一致"
        )
    if pinned.get("contentIndexSha256") != actual_index_hash:
        errors.append(
            "内容索引哈希漂移: content-index.json 已变化但 version.json 未重新固定"
        )
    return errors


def print_drift(errors: list[str]) -> None:
    print("VERSION_DRIFT")
    for item in errors:
        print(f"- {item}")
    print("")
    print("引导文件版本优先：请先更新 tools/lead-guide/version.json、content-index.json 和 persona，")
    print("再重新运行引导。当前不进入答题/审查流程。")


def load_stages(path: Path = STAGES_PATH) -> dict:
    data = read_json(path)
    stages = data.get("stages")
    if not isinstance(stages, list) or not stages:
        raise ValueError("stages.json 必须包含非空 stages 数组")
    for i, stage in enumerate(stages, 1):
        if not stage.get("questions"):
            raise ValueError(f"第 {i} 段没有 questions")
    return data


def render_answers(stages: dict, answers: dict[str, list[str]]) -> str:
    lines = ["# OpenRig Lead onboarding answers", ""]
    for stage in stages["stages"]:
        sid = stage["id"]
        lines.append(f"## {stage.get('title', sid)} (`{sid}`)")
        for q, a in zip(stage["questions"], answers.get(sid, [])):
            lines.append(f"- Q: {q}")
            lines.append(f"  A: {a.strip() if a.strip() else '<未填写>'}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def interactive_collect(stages: dict) -> dict[str, list[str]]:
    print(stages.get("brief", "").strip())
    print("")
    answers: dict[str, list[str]] = {}
    for stage in stages["stages"]:
        print(f"== {stage.get('title', stage['id'])} ==")
        stage_answers = []
        for q in stage["questions"]:
            print(q)
            answer = input("> ").strip()
            stage_answers.append(answer)
        answers[stage["id"]] = stage_answers
        print("")
    return answers


def parse_review(text: str) -> dict:
    """Parse the reviewer's structured block, tolerating surrounding prose."""
    verdict = ""
    final = ""
    missing = ""
    questions = ""
    explanation = ""
    present: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().upper()
        if key == "VERDICT":
            verdict = value.strip().upper()
        elif key == "FINAL":
            final = value.strip()
        elif key == "MISSING":
            missing = value.strip()
        elif key == "QUESTIONS":
            questions = value.strip()
        elif key == "EXPLANATION":
            explanation = value.strip()
        else:
            continue
        present.add(key)
    return {
        "verdict": verdict,
        "final": final,
        "missing": missing,
        "questions": questions,
        "explanation": explanation,
        "present": present,
        "raw": text,
    }


def build_review_prompt(persona: str, index: dict, stages: dict, answers_text: str) -> str:
    facts = []
    for item in index.get("entries", []):
        facts.append(f"- [{item.get('id')}] {item.get('title')}: {item.get('mustKnow')}")
    return f"""{persona}

## Content index (pinned)

OpenRig guide version: {index.get('openrigGuide', {}).get('version')}
Main document: {index.get('openrigGuide', {}).get('mainDoc')}

{chr(10).join(facts)}

## Onboarding answers to review

{answers_text}

## Output contract

Return a short review, then exactly these lines at the end:

VERDICT: PASS | SMALL_DEVIATION | LARGE_DEVIATION | INCOMPLETE
MISSING: <what is missing, or none>
QUESTIONS: <up to 3 key questions for small deviation, or none>
EXPLANATION: <one short paragraph; required when INCOMPLETE>
FINAL: <write exactly 引导完成 for PASS or an accepted small deviation; write exactly 请重新运行引导 for LARGE_DEVIATION or INCOMPLETE>

Rules:
- PASS means the Lead understands the layers, units, governance dimensions, aliases,
  clarification gate, safety boundaries, evidence/QA, and version-drift priority.
- SMALL_DEVIATION means the answer is mostly right but needs 1-3 key confirmations.
  Ask only those questions, and do not write 引导完成 until they are answered.
- LARGE_DEVIATION means a core model is wrong or missing; write 请重新运行引导.
- INCOMPLETE means answers are empty or unusable; explain what must be filled.
- Never invent the final string. It must be one of the two exact strings above.
"""


def default_reviewer_cmd() -> list[str]:
    override = os.environ.get("LEAD_GUIDE_REVIEWER_CMD", "").strip()
    if override:
        return shlex.split(override)
    return ["dsh", "--profile", "headless"]


def call_reviewer(prompt: str, reviewer_cmd: list[str] | None = None, timeout: int = 240) -> str:
    cmd = list(reviewer_cmd or default_reviewer_cmd())
    # Run outside the repo so a project AGENTS.md does not steer the reviewer.
    with tempfile.TemporaryDirectory(prefix="openrig-lead-guide-") as tmp:
        proc = subprocess.run(
            cmd + [prompt],
            cwd=tmp,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    combined = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    if proc.returncode != 0:
        raise RuntimeError(f"审查命令退出码 {proc.returncode}: {combined.strip()[:500]}")
    return combined.strip()


def write_result(workdir: Path, text: str) -> Path:
    path = workdir / "RESULT.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write exactly the contract string; no trailing newline or extra prose.
    path.write_text(text.rstrip(), encoding="utf-8")
    return path


def archive_run(
    workdir: Path,
    verdict: str,
    exit_code: int,
    answers_path: Path | None = None,
) -> Path | None:
    """Archive one review bundle under workdir/history/<timestamp>/.

    This is the Lead-guide analogue of the 40 guide's per-stage history: the
    answers, reviewer output, result, and follow-up questions are kept together
    so a later audit can reconstruct what the reviewer saw and returned.
    """
    try:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        dest = workdir / "history" / stamp
        dest.mkdir(parents=True, exist_ok=True)
        for name in ("review.txt", "RESULT.txt", "FOLLOWUP-QUESTIONS.md"):
            src = workdir / name
            if src.is_file():
                shutil.copy2(src, dest / name)
        if answers_path is not None and answers_path.is_file():
            shutil.copy2(answers_path, dest / "answers.md")
        meta = {
            "archivedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
            "verdict": verdict,
            "exitCode": exit_code,
        }
        (dest / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return dest
    except OSError as exc:
        print(f"归档失败（不阻断结论）: {exc}")
        return None


def finalize(
    workdir: Path,
    text: str,
    verdict: str,
    exit_code: int,
    answers_path: Path | None = None,
) -> int:
    write_result(workdir, text)
    archive_run(workdir, verdict, exit_code, answers_path)
    return exit_code


def review(args: argparse.Namespace) -> int:
    drift = check_version()
    if drift:
        print_drift(drift)
        return EXIT_DRIFT

    stages = load_stages()
    workdir = Path(args.workdir).resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    answers_path = Path(args.answers).resolve() if args.answers else workdir / "answers.md"
    if not answers_path.is_file():
        print(f"缺少答题文件: {answers_path}")
        print("先运行 guide.py run 填写，或把答案写到该文件。")
        text = "未完成：缺少答题文件，无法开始审查。"
        return finalize(workdir, text, "INCOMPLETE", EXIT_INCOMPLETE)

    answers_text = answers_path.read_text(encoding="utf-8")
    if not answers_text.strip() or answers_text.count("<未填写>") == sum(
        len(s["questions"]) for s in stages["stages"]
    ):
        print("答案文件为空或全部未填写。")
        return finalize(
            workdir,
            "未完成：答案文件为空或全部未填写。",
            "INCOMPLETE",
            EXIT_INCOMPLETE,
            answers_path,
        )

    persona = PERSONA_PATH.read_text(encoding="utf-8")
    index = read_json(INDEX_PATH)
    prompt = build_review_prompt(persona, index, stages, answers_text)

    print("启动无头审查子智能体……")
    try:
        raw = call_reviewer(prompt, timeout=args.timeout)
    except subprocess.TimeoutExpired:
        print("审查子智能体超时。")
        return finalize(
            workdir,
            "未完成：审查子智能体超时，未能给出结论。",
            "INCOMPLETE",
            EXIT_INCOMPLETE,
            answers_path,
        )
    except FileNotFoundError as exc:
        print(f"审查命令不可用: {exc}")
        return finalize(
            workdir,
            "未完成：审查命令不可用。",
            "INCOMPLETE",
            EXIT_INCOMPLETE,
            answers_path,
        )
    except RuntimeError as exc:
        print(f"审查命令失败: {exc}")
        return finalize(
            workdir,
            "未完成：审查命令失败，未能给出可信结论。",
            "INCOMPLETE",
            EXIT_INCOMPLETE,
            answers_path,
        )

    parsed = parse_review(raw)
    (workdir / "review.txt").write_text(raw + "\n", encoding="utf-8")
    print(f"审查结论: {parsed['verdict'] or 'UNKNOWN'}")

    absent = [field for field in REQUIRED_REVIEW_FIELDS if field not in parsed["present"]]
    if absent:
        text = f"未完成：审查输出缺少必需字段 {', '.join(absent)}，请重新运行引导或检查审查命令。"
        print(text)
        return finalize(workdir, text, "INCOMPLETE", EXIT_INCOMPLETE, answers_path)

    if parsed["verdict"] == VERDICT_PASS and parsed["final"] == FINAL_OK:
        print(FINAL_OK)
        return finalize(workdir, FINAL_OK, parsed["verdict"], EXIT_OK, answers_path)

    if parsed["verdict"] == VERDICT_SMALL:
        questions = parsed["questions"].strip()
        if not questions or questions.lower() == "none":
            questions = (
                "请确认："
                + (parsed["missing"] or parsed["explanation"] or "审查指出了小偏差，但未列出具体问题。")
            )
        question_path = workdir / "FOLLOWUP-QUESTIONS.md"
        question_path.write_text(
            "# 需要确认的关键问题\n\n" + questions + "\n", encoding="utf-8"
        )
        print(f"偏差较小，请先回答关键问题: {question_path}")
        if args.interactive and sys.stdin.isatty():
            with question_path.open("a", encoding="utf-8") as f:
                f.write("\n## 回答\n\n")
                for q in [x.strip() for x in questions.split(";") if x.strip()]:
                    print(q)
                    f.write(f"- Q: {q}\n  A: {input('> ').strip()}\n")
            with answers_path.open("a", encoding="utf-8") as f:
                f.write("\n## 复查补充\n\n" + question_path.read_text(encoding="utf-8"))
            archive_run(workdir, parsed["verdict"], EXIT_SMALL_DEVIATION, answers_path)
            args.interactive = False
            return review(args)
        text = "偏差较小，但尚未确认关键问题。请回答 FOLLOWUP-QUESTIONS.md 后重新运行 review。"
        return finalize(
            workdir, text, parsed["verdict"], EXIT_SMALL_DEVIATION, answers_path
        )

    if parsed["verdict"] == VERDICT_LARGE:
        print(FINAL_RERUN)
        return finalize(workdir, FINAL_RERUN, parsed["verdict"], EXIT_USAGE, answers_path)

    if parsed["verdict"] == VERDICT_INCOMPLETE:
        explanation = parsed.get("explanation") or parsed.get("missing") or "答案不完整。"
        text = f"未完成：{explanation}"
        print(text)
        return finalize(workdir, text, parsed["verdict"], EXIT_INCOMPLETE, answers_path)

    text = "未完成：审查输出缺少可识别的 VERDICT/FINAL 行，请重新运行引导或检查审查命令。"
    print("审查输出格式不可识别，未通过。")
    return finalize(workdir, text, "INCOMPLETE", EXIT_INCOMPLETE, answers_path)


def run(args: argparse.Namespace) -> int:
    drift = check_version()
    if drift:
        print_drift(drift)
        return EXIT_DRIFT

    stages = load_stages()
    workdir = Path(args.workdir).resolve()
    workdir.mkdir(parents=True, exist_ok=True)

    if args.answers:
        answers_path = Path(args.answers).resolve()
        if not answers_path.is_file():
            print(f"缺少答题文件: {answers_path}")
            return EXIT_USAGE
        target = workdir / "answers.md"
        target.write_text(answers_path.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        if not sys.stdin.isatty():
            print("非交互环境：请提供 --answers FILE，或把答案写到 run/answers.md 后运行 review。")
            return EXIT_USAGE
        answers = interactive_collect(stages)
        target = workdir / "answers.md"
        target.write_text(render_answers(stages, answers), encoding="utf-8")

    print(f"答案已写入: {target}")
    print("开始无头审查……")
    sub = argparse.Namespace(
        workdir=str(workdir),
        answers=str(target),
        timeout=args.timeout,
        interactive=not args.non_interactive,
    )
    return review(sub)


def check_version_cmd(_: argparse.Namespace) -> int:
    drift = check_version()
    if drift:
        print_drift(drift)
        return EXIT_DRIFT
    pinned = read_json(VERSION_PATH)
    print("VERSION_OK")
    print(f"guideVersion={pinned.get('guideVersion')}")
    print(f"openrigGuideVersion={pinned.get('openrigGuideVersion')}")
    print(f"mainDocSha256={pinned.get('mainDocSha256')}")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OpenRig Lead onboarding guide")
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check-version", help="verify the guide is pinned to the current main doc")
    p_check.set_defaults(func=check_version_cmd)

    p_run = sub.add_parser("run", help="fill stages interactively (or from --answers) and review")
    p_run.add_argument("--workdir", default="run")
    p_run.add_argument("--answers")
    p_run.add_argument("--timeout", type=int, default=240)
    p_run.add_argument("--non-interactive", action="store_true")
    p_run.set_defaults(func=run)

    p_review = sub.add_parser("review", help="review an existing answers file with a headless agent")
    p_review.add_argument("--workdir", default="run")
    p_review.add_argument("--answers")
    p_review.add_argument("--timeout", type=int, default=240)
    p_review.add_argument("--interactive", action="store_true")
    p_review.set_defaults(func=review)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
