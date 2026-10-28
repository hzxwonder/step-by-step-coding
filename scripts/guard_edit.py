#!/usr/bin/env python3
"""Claude Code 可选 PreToolUse 文件写入范围守卫，stdin 为工具 JSON 输入。"""
import json
import os
import sys
from pathlib import Path


def denied(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                            "permissionDecisionReason": "人机协作步骤门禁：" + reason}}, ensure_ascii=False))


def is_inside(path, root):
    try:
        return path.relative_to(root)
    except ValueError:
        return None


def check(payload, repo):
    name = payload.get("tool_name", "")
    if name not in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        return None  # 钩子不会覆盖 Bash、外部脚本或其他写入工具
    active = repo / ".ai-collab" / "active.json"
    if not active.is_file():
        return None  # 尚未启用本工作流时不影响其它任务
    try:
        slug = json.loads(active.read_text(encoding="utf-8"))["slug"]
        state = json.loads((repo / ".ai-collab" / slug / "state.json").read_text(encoding="utf-8"))
    except (KeyError, ValueError, OSError):
        return "工作流状态不可用，保守拒绝编辑。请检查状态文件"

    inp = payload.get("tool_input", {})
    target = inp.get("file_path") or inp.get("notebook_path")
    if not isinstance(target, str) or not target:
        return "无法识别目标文件路径，保守拒绝写入"
    target_path = Path(target)
    if not target_path.is_absolute():
        target_path = Path(payload.get("cwd") or repo) / target_path
    rel = is_inside(target_path.resolve(), repo)
    if rel is None:
        return "目标文件不在当前项目中"
    relative = rel.as_posix()

    if relative.startswith(".git/") or relative.startswith(".ai-collab/"):
        return "禁止通过普通编辑工具更改 .git 或审批状态"
    base = Path(relative).name
    if base == ".env" or base.startswith(".env.") or base in ("id_rsa", "id_ed25519"):
        return "敏感文件不在常规编程白名单中"

    base_dir = f"docs/ai-collab/{slug}/"
    step_prefix = base_dir + f"steps/{int(state['current_step']):02d}-step/"
    phase = state["phase"]
    design_paths = {base_dir + name for name in ("plan.md", "mvp-design.md", "technical-plan.md", "prototype.html")}
    if phase == "planning":
        if relative in design_paths or (relative.startswith(base_dir + "steps/") and relative.endswith("/plan.md")):
            return None
        return "设计阶段可编写当前任务的设计、技术方案、计划与 HTML 原型；业务实现须先获授权"
    if phase in ("await_git_preference", "await_step_authorization", "await_next_step"):
        planned_step = int(state["current_step"]) + 1 if phase == "await_next_step" else 1
        next_plan = base_dir + f"steps/{planned_step:02d}-step/plan.md"
        if relative in design_paths | {next_plan}:
            return None
    if phase == "implementing":
        allowed = set(state.get("allowed_paths", {}).get(str(state["current_step"]), []))
        if relative in allowed or relative in {step_prefix + "plan.md", step_prefix + "verification.md", step_prefix + "explain.md", step_prefix + "preacceptance.md"}:
            return None
        return f"仅允许步骤 {state['current_step']} 获批文件；{relative} 未授权"
    if phase in ("explaining", "precheck_setup"):
        if relative in {step_prefix + "explain.md", step_prefix + "verification.md", step_prefix + "preacceptance.md"}:
            return None
        return "讲解/预验收准备阶段不能修改代码；仅允许本步骤的讲解、验证和题库文档"
    if phase in ("precheck", "precheck_discussion", "await_acceptance", "await_next_step"):
        if relative in {step_prefix + "explain.md", step_prefix + "verification.md"}:
            return None
        return "预验收题库已锁定或本步已结束；不能改代码或题目。需要修改请先按流程重设/修订"
    return "目前阶段不允许写文件，必须得到用户对当前步骤的明确授权"


def main():
    try:
        payload = json.load(sys.stdin)
        cwd = Path(os.environ.get("CLAUDE_PROJECT_DIR", payload.get("cwd", "."))).resolve()
        reason = check(payload, cwd)
        if reason:
            denied(reason)
    except Exception as exc:
        denied(f"检查程序异常，安全起见拒绝：{exc}")


if __name__ == "__main__":
    main()
