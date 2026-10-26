#!/usr/bin/env python3
"""辅助状态机：不接触远程、不会自动写业务代码。Python 3.9+，无三方依赖。"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
VALID_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
PRECHECK_SCHEMA = "alignment-mcq-v2"


def fail(message):
    raise SystemExit("操作已阻止：" + message)


def run_git(repo, *args):
    process = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True)
    if process.returncode != 0:
        fail("Git 操作失败：" + (process.stderr.strip() or " ".join(args)))
    return process.stdout.strip()


def project_dir(repo, slug):
    return repo / "docs" / "ai-collab" / slug


def state_file(repo, slug):
    return repo / ".ai-collab" / slug / "state.json"


def active_file(repo):
    return repo / ".ai-collab" / "active.json"


def load(repo):
    ap = active_file(repo)
    if not ap.is_file():
        fail("未发现活动任务，请先运行 init")
    slug = json.loads(ap.read_text(encoding="utf-8"))["slug"]
    sp = state_file(repo, slug)
    if not sp.is_file():
        fail("状态文件缺失")
    return json.loads(sp.read_text(encoding="utf-8"))


def save(repo, state, message):
    state.setdefault("history", []).append({"time": datetime.now(timezone.utc).isoformat(), "action": message})
    path = state_file(repo, state["slug"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def step_folder(repo, state, n):
    return project_dir(repo, state["slug"]) / "steps" / f"{n:02d}-step"


def current_folder(repo, state):
    return step_folder(repo, state, state["current_step"])


def template_file(name, values):
    text = (SKILL_ROOT / "assets" / name).read_text(encoding="utf-8")
    for k, v in values.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text


def empty_precheck():
    return {"schema": PRECHECK_SCHEMA, "questions": [], "baselines": {},
            "results": {}, "attempts": [], "file_hash": None, "source_hashes": {}}


def cmd_init(repo, a):
    if not VALID_SLUG.fullmatch(a.slug):
        fail("slug 只能包含小写字母、数字和连字符")
    if a.steps < 1 or a.steps > 99:
        fail("steps 必须在 1–99 之间")
    if active_file(repo).exists():
        fail("已有活动任务。为避免覆盖，请先手工归档已有任务并确认，再启动新任务。")
    base = project_dir(repo, a.slug)
    if base.exists():
        fail("任务文档目录已存在，不会覆盖")
    base.mkdir(parents=True)
    master_text = template_file("master-plan.md", {"TASK_TITLE": a.title, "TASK_SLUG": a.slug})
    sample_rows = r"(?m)^\| 01 \|[^\n]*\n\| 02 \|[^\n]*\n"
    rows = "".join(f"| {i:02d} | 待讨论 | 需填具体缺口及后果 | 需填对总目标的具体贡献 | 待验证 | 待确认依赖 | 未授权 |\n" for i in range(1, a.steps + 1))
    master_text, count = re.subn(sample_rows, lambda _: rows, master_text)
    if count != 1:
        fail("总计划模板中的步骤表格式不符合预期")
    (base / "plan.md").write_text(master_text, encoding="utf-8")
    for n in range(1, a.steps + 1):
        folder = step_folder(repo, {"slug": a.slug}, n)
        folder.mkdir(parents=True)
        (folder / "plan.md").write_text(template_file("step-plan.md", {"STEP": f"{n:02d}", "STEP_TITLE": "待讨论"}), encoding="utf-8")
    state = {
        "slug": a.slug, "title": a.title, "phase": "planning", "total_steps": a.steps,
        "current_step": 1, "allowed_paths": {str(i): [] for i in range(1, a.steps + 1)},
        "accepted_steps": [], "git": {"mode": "undecided", "platform": None, "remote": None, "branch": None},
        "push_records": [], "precheck": empty_precheck(), "history": []
    }
    active_file(repo).parent.mkdir(parents=True, exist_ok=True)
    active_file(repo).write_text(json.dumps({"slug": a.slug}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    save(repo, state, "初始化计划文件（尚无代码授权）")
    print(f"已生成总 plan.md 和 {a.steps} 个子 plan.md；目前仅能规划。")


def need(state, *phases):
    if state["phase"] not in phases:
        fail(f"当前 phase={state['phase']}，此操作只允许在 {', '.join(phases)}")


# 这些结构化检查只阻止空白/占位计划；理由是否真实合理仍需用户判断。
WHY_KEYS = ("当前问题", "不做的后果", "安排在此时的原因")
ROLE_KEYS = ("对总目标的贡献", "承接什么", "为后续提供什么", "可验证的阶段成果")


def section_content(text, heading):
    match = re.search(r"(?m)^##\s+\d+\.\s+" + re.escape(heading) + r"\s*$", text)
    if not match:
        return None
    rest = text[match.end():]
    next_heading = re.search(r"(?m)^##\s+\d+\.\s+", rest)
    return rest[:next_heading.start()] if next_heading else rest


def missing_reasoning(text, step):
    missing = []
    for title, fields in (("为什么需要这一步", WHY_KEYS), ("这一步在整个项目中的作用", ROLE_KEYS)):
        block = section_content(text, title)
        if block is None:
            missing.append(f"{title}（缺少章节）")
            continue
        for name in fields:
            matches = re.findall(r"(?m)^-\s+\*\*" + re.escape(name) + r"\*\*：([^\n]*)$", block)
            if len(matches) != 1 or not substantial_reason(matches[0]):
                missing.append(f"{title} → {name}")
    return missing


def substantial_reason(value):
    value = value.strip()
    if len(value) < 8:
        return False
    if value.startswith(("（", "(", "[", "<")) or any(x in value for x in ("{{", "}}", "待讨论", "待填写", "TODO", "...", "……", "需填", "占位")):
        return False
    if value in ("为了后续开发", "完善功能", "提高质量", "以后再说"):
        return False
    return True


def validate_plan_reasons(repo, state, step=None):
    master = project_dir(repo, state["slug"]) / "plan.md"
    if not master.is_file():
        fail("总 plan.md 缺失")
    master_text = master.read_text(encoding="utf-8")
    header = "| 编号 | 子任务 | 为什么需要这一步 | 在整个项目中的作用 |"
    if header not in master_text:
        fail("总 plan.md 必须有每一步‘为什么需要’和‘在整个项目中的作用’两列")
    steps = [step] if step is not None else range(1, state["total_steps"] + 1)
    for n in steps:
        # 检查总览表里每步有一行具体的理由与职责（详细论证在各自的 plan.md）
        matches = [r for r in master_text.splitlines()
                   if re.match(r"^\|\s*0?" + str(n) + r"\s*\|", r)]
        if len(matches) != 1:
            fail(f"总计划步骤 {n:02d} 缺少唯一的汇总行")
        cols = [c.strip() for c in matches[0].strip().strip("|").split("|")]
        if len(cols) < 7 or not substantial_reason(cols[2]) or not substantial_reason(cols[3]):
            fail(f"总计划步骤 {n:02d} 的‘为什么需要/在全局中作用’必须填入具体内容")
        detail = step_folder(repo, state, n) / "plan.md"
        if not detail.is_file():
            fail(f"步骤 {n:02d} 的 plan.md 缺失")
        missing = missing_reasoning(detail.read_text(encoding="utf-8"), n)
        if missing:
            fail(f"步骤 {n:02d} 的 plan.md 未说明必要性/全局作用：" + "; ".join(missing) + "；请先与用户讨论并补完")


def cmd_approve_plan(repo, state, a):
    need(state, "planning")
    plans = [step_folder(repo, state, n) / "plan.md" for n in range(1, state["total_steps"] + 1)]
    if any(not p.is_file() for p in plans):
        fail("每一步都必须有独立 plan.md")
    validate_plan_reasons(repo, state)
    if not a.user_quote.strip():
        fail("必须记录用户明确批准计划的原话")
    state["phase"] = "await_git_preference"
    save(repo, state, "用户批准全局及各步骤计划：" + a.user_quote)
    print("计划已批准。编码前，请单独问用户是否要每步推送到 GitHub / GitCode。")


def cmd_allow_path(repo, state, a):
    need(state, "planning", "await_git_preference", "await_step_authorization", "await_next_step", "implementing")
    if a.step < 1 or a.step > state["total_steps"]:
        fail("步骤编号不存在")
    if state["phase"] == "implementing" and a.step != state["current_step"]:
        fail("实施时只能调整当前步骤路径，需用户单独批准范围变化")
    p = Path(a.path)
    if p.is_absolute() or ".." in p.parts or a.path.startswith(".git/") or a.path.startswith(".ai-collab/"):
        fail("不允许绝对路径、上级跳转、.git 或工作流内部状态")
    if not a.path.strip() or any(c in a.path for c in "*?[]"):
        fail("必须使用精确相对路径，不允许通配符")
    normalized = p.as_posix().lstrip("./")
    paths = state["allowed_paths"][str(a.step)]
    if normalized not in paths:
        paths.append(normalized)
    save(repo, state, f"登记步骤 {a.step} 的获批改动路径：{normalized}")
    print("已登记路径；实际需在该步骤 plan.md 中列明，并经过用户批准。")


def cmd_configure_git(repo, state, a):
    need(state, "await_git_preference")
    if a.mode == "per-step":
        if not all([a.platform, a.remote, a.branch]):
            fail("启用推送必须依次与用户确认 platform / remote / branch")
        if a.platform not in ("github", "gitcode"):
            fail("platform 必须是 github 或 gitcode")
        if a.branch in ("main", "master") and not a.allow_protected:
            fail("默认禁止直接推送 main/master；需要额外明确授权才可打开")
        if re.search(r"[\s~^:?*\[\\]", a.branch) or a.branch.startswith("-") or ".." in a.branch:
            fail("无效分支名称")
        if not a.user_quote.strip():
            fail("需要记录用户确认推送方式的原话")
        run_git(repo, "rev-parse", "--show-toplevel")
        run_git(repo, "remote", "get-url", a.remote)
        state["git"] = {"mode": "per-step", "platform": a.platform, "remote": a.remote, "branch": a.branch}
    else:
        state["git"] = {"mode": "off", "platform": None, "remote": None, "branch": None}
    state["phase"] = "await_step_authorization"
    save(repo, state, "用户 Git 决策：" + (a.user_quote or "仅保留本地"))
    print("Git 决策已记录。仍不能写代码：必须等待用户授权第 1 步。")


def cmd_authorize(repo, state, a):
    need(state, "await_step_authorization", "await_next_step")
    expected = 1 if state["phase"] == "await_step_authorization" else state["current_step"] + 1
    if a.step != expected:
        fail(f"只能授权第 {expected} 步（当前或此前步骤不能跳跃）")
    if a.step > state["total_steps"]:
        fail("没有更多步骤")
    if not a.user_quote.strip():
        fail("必须记录用户明确要求实施本步骤的原话")
    validate_plan_reasons(repo, state, step=a.step)
    if not state["allowed_paths"].get(str(a.step)):
        fail("本步骤尚未登记精确获批文件路径；即使新建文件也要列出")
    if expected > 1 and expected - 1 not in state["accepted_steps"]:
        fail("上一步骤尚未验收")
    state["precheck"] = empty_precheck()
    state["current_step"] = expected
    state["phase"] = "implementing"
    save(repo, state, f"用户授权实施步骤 {expected}：{a.user_quote}")
    print(f"已授权步骤 {expected}；只能修改其已登记的文件及自身文档。")


def cmd_verified(repo, state, a):
    need(state, "implementing")
    path = current_folder(repo, state) / "verification.md"
    if not path.is_file():
        fail("请先生成当前步骤 verification.md，并记录实际测试命令和结果")
    if a.result != "pass":
        fail("测试未通过或受阻不能进入正常验收；请保留证据并与用户讨论")
    state["phase"] = "explaining"
    save(repo, state, f"步骤 {state['current_step']} 的验证自报通过：{a.evidence}")
    print("已进入讲解阶段。必须制作 explain.md 并与用户讨论。")


def cmd_documented(repo, state, a):
    need(state, "explaining")
    p = current_folder(repo, state) / "explain.md"
    if not p.is_file() or len(p.read_text(encoding="utf-8")) < 300:
        fail("请先生成有实质内容的 explain.md")
    state["phase"] = "precheck_setup"
    save(repo, state, "当前步骤讲解文档已生成；进入预验收问题准备阶段")
    print("讲解已就绪；整理必要的行为确认项，沿用明确的原话，只询问尚未解决的决定。")



def precheck_file(repo, state):
    return current_folder(repo, state) / "preacceptance.md"


def file_digest(path):
    if not path.is_file():
        fail("预验收问题文件缺失，禁止评分或验收")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_source_hashes(repo, state):
    """记录规划、解释、验证与获批源码的指纹，防止用旧预验收验新代码。"""
    folder = current_folder(repo, state)
    required = [folder / f for f in ("plan.md", "verification.md", "explain.md")]
    required.append(project_dir(repo, state["slug"]) / "plan.md")
    optional = [repo / item for item in state["allowed_paths"][str(state["current_step"])]]
    result = {}
    for file in required + optional:
        if file.name.startswith("preacceptance-results"):
            continue  # 用户回答是可变工作流记录，不属于待验证源码
        relative = file.relative_to(repo).as_posix()
        if not file.exists():
            if file in required:
                fail(f"预验收必备文档缺失：{file}")
            # 获批修改的文件可以最终无需创建；记录不存在状态以检测后续新建
            result[relative] = "<missing>"
            continue
        if not file.is_file():
            fail(f"预验收证据必须为普通文件：{file}")
        result[relative] = hashlib.sha256(file.read_bytes()).hexdigest()
    return result


def assert_source_unchanged(repo, state):
    previous = state.get("precheck", {}).get("source_hashes", {})
    if not previous or previous != collect_source_hashes(repo, state):
        fail("本步骤计划、验证文档、讲解或源码在锁题后发生变化；须 revise 重新验证、生成讲解、再开始预验收")


def write_precheck_results(repo, state):
    """只保存真实用户的选择；不把方案偏好作为知识考试来打分。"""
    pre = state["precheck"]
    lines = [f"# 第 {state['current_step']} 步 · 需求对齐预验收记录（本地）", "",
             "> 本文档可能包含用户原话，默认不得推送 GitHub/GitCode。",
             "> 选择题和当前已批准的方案见锁定的 `preacceptance.md`。",
             "> 选项与现有方案不同不是答错；说明存在值得讨论的需求分歧。", ""]
    for i, rec in enumerate(pre.get("attempts", []), start=1):
        label = "已对齐" if rec["result"] == "aligned" else "需要讨论"
        lines += [f"## 第 {i} 次选择 · {rec['id']} · {label}", "",
                  f"- 用户选择：**{rec['choice']}**",
                  f"- 当前方案：**{rec['baseline']}**",
                  f"- 用户原话：{rec['user_answer']}",
                  f"- 对齐说明：{rec['summary']}",
                  f"- 需求/代码证据：{rec['evidence']}", ""]
    passed = len(pre.get("results", {}))
    lines += ["## 当前对齐状态", "", f"- 已对齐：{passed} / {len(pre['questions'])}",
              f"- 待确认：{', '.join(q for q in pre['questions'] if q not in pre['results']) or '无'}", "",
              "所有题目对齐之后，仍需用户单独确认正式验收；正式验收不代表开始下一步。", ""]
    path = current_folder(repo, state) / "preacceptance-results.md"
    path.write_text("\n".join(lines), encoding="utf-8")


def validate_question_file(path):
    if not path.is_file():
        fail("请先在当前步骤目录创建 preacceptance.md")
    content = path.read_text(encoding="utf-8")
    if any(tag in content for tag in ("<填写", "<关键点", "<替换", "{{")):
        fail("预验收文件还有模板占位文字，请用本步已验证需求和代码证据替换")
    headings = list(re.finditer(r"(?m)^### (Q[1-9][0-9]*)\s+([^\n]+)$", content))
    questions = [m.group(1) for m in headings]
    if not 1 <= len(questions) <= 6:
        fail("请记录 1–6 项必要的行为约定；已有明确原话的项目无需重问")
    if questions != [f"Q{i}" for i in range(1, len(questions) + 1)]:
        fail("题号必须从 Q1 连续编号")
    baseline_map = {}
    option_map = {}
    for i, match in enumerate(headings):
        block = content[match.end():headings[i + 1].start() if i + 1 < len(headings) else len(content)]
        options = re.findall(r"(?m)^- ([ABCD])\.\s+([^\n]+)$", block)
        keys = [k for k, _ in options]
        if keys not in (["A", "B", "D"], ["A", "B", "C", "D"]):
            fail(f"{questions[i]} 需要两个或三个实际行为选项，并保留 D 作为讨论出口")
        labels = [v.strip() for _, v in options]
        if any(len(v) < 3 for v in labels) or len(set(labels)) != len(labels):
            fail(f"{questions[i]} 选项必须具体、不重复，且不能为空")
        if not any(t in labels[-1] for t in ("其他", "不确定", "需要讨论", "不符合")):
            fail(f"{questions[i]} 的 D 选项必须允许用户表达不确定、其他期望或需要讨论")
        baseline = re.findall(r"(?m)^- \*\*当前约定选项\*\*：([ABCD])\s*$", block)
        if len(baseline) != 1 or baseline[0] not in keys[:-1]:
            fail(f"{questions[i]} 的当前约定必须对应一个实际提供的行为选项")
        for field in ("**证据**", "**分歧处理**"):
            if field not in block:
                fail(f"{questions[i]} 缺少 {field}，不能开始预验收")
        baseline_map[questions[i]] = baseline[0]
        option_map[questions[i]] = keys
    return questions, baseline_map, option_map


def question_hashes(path):
    """逐项比较行为约定；证据与讨论说明更新不撤销用户选择。"""
    content = path.read_text(encoding="utf-8")
    blocks = re.split(r"(?m)(?=^### Q[1-9][0-9]*\s)", content)[1:]
    return {re.match(r"### (Q[1-9][0-9]*)", block).group(1):
            hashlib.sha256(block.split("- **证据**", 1)[0].strip().encode()).hexdigest()
            for block in blocks}


def invalidate_affected(repo, state, affected):
    pre = state["precheck"]
    if any(q not in pre["questions"] for q in affected):
        fail("受影响题号必须属于当前步骤题库")
    if pre["questions"] and precheck_file(repo, state).is_file() and not pre.get("question_hashes") and pre.get("file_hash") == file_digest(precheck_file(repo, state)):
        pre["question_hashes"] = question_hashes(precheck_file(repo, state))
    for q in affected:
        pre["results"].pop(q, None)


def cmd_start_precheck(repo, state, a):
    need(state, "precheck_setup")
    path = precheck_file(repo, state)
    questions, baselines, options = validate_question_file(path)
    hashes = question_hashes(path)
    previous = state.get("precheck") or empty_precheck()
    old_hashes = previous.get("question_hashes", {})
    same_file = previous.get("file_hash") == file_digest(path)
    retained = {q: record for q, record in previous["results"].items()
                if q in questions and record.get("result") == "aligned"
                and record.get("choice") == baselines[q]
                and (old_hashes.get(q) == hashes[q] or (not old_hashes and same_file))}
    state["precheck"] = {"schema": PRECHECK_SCHEMA, "questions": questions, "baselines": baselines,
                         "options": options,
                         "results": retained, "attempts": previous["attempts"],
                         "question_hashes": hashes, "file_hash": file_digest(path),
                         "source_hashes": collect_source_hashes(repo, state)}
    pending = [q for q in questions if q not in retained]
    state["phase"] = "precheck" if pending else "await_acceptance"
    write_precheck_results(repo, state)
    save(repo, state, f"当前约定已锁定；保留 {len(retained)} 项确认，待确认 {len(pending)} 项")
    print(f"只确认 {pending[0]}，其余已有确认沿用。" if pending else "已有确认均适用；可请求本步骤正式验收。")


def cmd_answer_precheck(repo, state, a):
    need(state, "precheck")
    pre = state.get("precheck") or {}
    if pre.get("schema") != PRECHECK_SCHEMA:
        fail("发现旧版知识问答状态；请经用户同意 reset-precheck 后使用新的选择题格式")
    if pre.get("file_hash") != file_digest(precheck_file(repo, state)):
        fail("选择题或当前约定已变更。请经用户同意 reset-precheck 并重新对齐")
    assert_source_unchanged(repo, state)
    remaining = [x for x in pre["questions"] if x not in pre["results"]]
    if not remaining or a.id != remaining[0]:
        fail("必须逐题确认，当前应为 " + (remaining[0] if remaining else "无"))
    if a.choice not in pre.get("options", {}).get(a.id, list("ABCD")):
        fail("该确认项未提供这个选项；请保留用户原话，先澄清实际期望")
    for field in ("user_answer", "summary", "evidence"):
        if not getattr(a, field, "").strip():
            fail("必须记录用户真实选择、简短对齐说明与具体需求/实现证据")
    baseline = pre["baselines"].get(a.id)
    if baseline not in ("A", "B", "C"):
        fail("当前约定选项无效，不能自动对齐")
    aligned = a.choice == baseline and not a.needs_discussion
    record = {"id": a.id, "choice": a.choice, "baseline": baseline,
              "result": "aligned" if aligned else "discussion",
              "user_answer": a.user_answer, "summary": a.summary, "evidence": a.evidence}
    pre["attempts"].append(record)
    if aligned:
        pre["results"][a.id] = record
        state["phase"] = "await_acceptance" if len(pre["results"]) == len(pre["questions"]) else "precheck"
    else:
        state["phase"] = "precheck_discussion"
    write_precheck_results(repo, state)
    save(repo, state, f"对齐题 {a.id}：选 {a.choice}；当前约定 {baseline}；{record['result']}")
    if not aligned:
        print("出现需求分歧或不确定：这不是答错。暂停后续问题，解释当前方案、代码和差别；用户明确决定保留则 resume-precheck 记录该次确认，决定修改则 revise 后重新验证。")
    elif state["phase"] == "await_acceptance":
        print("所有关键细节已与当前方案对齐。请总结对齐结果，再单独询问用户是否正式验收本步骤。")
    else:
        upcoming = [x for x in pre["questions"] if x not in pre["results"]][0]
        print(f"本题已对齐，下一轮只问 {upcoming}。")


def cmd_resume_precheck(repo, state, a):
    need(state, "precheck_discussion")
    if not a.user_quote.strip():
        fail("必须记录用户解决分歧、明确选择保留当前已批准方案的原话")
    if state.get("precheck", {}).get("file_hash") != file_digest(precheck_file(repo, state)):
        fail("题库发生变化，必须重设预验收")
    assert_source_unchanged(repo, state)
    state["phase"] = "precheck"
    pre = state["precheck"]
    q = next(q for q in pre["questions"] if q not in pre["results"])
    cmd_answer_precheck(repo, state, argparse.Namespace(
        id=q, choice=pre["baselines"][q], user_answer=a.user_quote,
        summary="用户讨论后明确确认当前行为", evidence=pre["attempts"][-1]["evidence"],
        needs_discussion=False))


def cmd_reset_precheck(repo, state, a):
    need(state, "precheck", "precheck_discussion", "await_acceptance", "precheck_setup")
    if not a.user_quote.strip():
        fail("需要记录用户允许调整题目的明确表述")
    invalidate_affected(repo, state, a.affected)
    state["phase"] = "precheck_setup"
    save(repo, state, "调整题库，保留未变化的确认：" + a.user_quote)
    print("修改问题后执行 start-precheck；只补充变化或尚未解决的项目。")


def cmd_revise(repo, state, a):
    need(state, "precheck_setup", "precheck", "precheck_discussion", "await_acceptance", "explaining", "await_next_step", "completed")
    if not a.user_quote.strip():
        fail("必须记录用户要求修订当前步骤的原话")
    invalidate_affected(repo, state, a.affected)
    if state["current_step"] in state["accepted_steps"]:
        state["accepted_steps"].remove(state["current_step"])
    state["phase"] = "implementing"
    save(repo, state, "修订当前步骤，验证受影响实现并保留未变化的确认：" + a.user_quote)
    print("修改后验证受影响实现、更新讲解；只确认新增、变化或尚未解决的行为。")


def cmd_accept(repo, state, a):
    need(state, "await_acceptance")
    pre = state.get("precheck", {})
    qs = pre.get("questions", [])
    passed = pre.get("results", {})
    if pre.get("schema") != PRECHECK_SCHEMA or not 1 <= len(qs) <= 6 or any(passed.get(q, {}).get("result") != "aligned" for q in qs):
        fail("核心需求细节尚未全部由用户逐题选择并确认对齐，禁止正式验收")
    if pre.get("file_hash") != file_digest(precheck_file(repo, state)):
        fail("预验收题库被修改，需重设并重新逐题预验收")
    assert_source_unchanged(repo, state)
    if not a.user_quote.strip():
        fail("必须记录用户明确验收通过的原话")
    if state["current_step"] not in state["accepted_steps"]:
        state["accepted_steps"].append(state["current_step"])
    state["phase"] = "await_push" if state["git"]["mode"] == "per-step" else next_phase(state)
    save(repo, state, f"用户明确验收步骤 {state['current_step']}：{a.user_quote}")
    print("本步已验收。" + ("请按已确认目标安全 push 并记录结果。" if state["phase"] == "await_push" else "停下；后续需要单独授权。"))


def next_phase(state):
    return "completed" if state["current_step"] >= state["total_steps"] else "await_next_step"


def cmd_pushed(repo, state, a):
    need(state, "await_push")
    git_cfg = state["git"]
    if git_cfg["mode"] != "per-step":
        fail("用户未启用推送")
    if not a.success:
        fail("推送尚未真实成功，不得记录完成")
    current_sha = run_git(repo, "rev-parse", "HEAD")
    if a.commit != current_sha:
        fail("记录的提交 SHA 与当前 HEAD 不一致")
    state["push_records"].append({"step": state["current_step"], "commit": a.commit,
                                  "remote": git_cfg["remote"], "branch": git_cfg["branch"]})
    state["phase"] = next_phase(state)
    save(repo, state, f"用户已选择的推送流程完成，步骤 {state['current_step']}，commit={a.commit}")
    print("已记录推送成功。请停下；不得自行实现下一步。")


def cmd_status(repo, state, a):
    print(json.dumps({k: v for k, v in state.items() if k != "history"}, indent=2, ensure_ascii=False))
    print("\n总计划：", project_dir(repo, state["slug"]) / "plan.md")
    print("当前步骤计划：", current_folder(repo, state) / "plan.md")


def parser():
    p = argparse.ArgumentParser(description="Step-by-Step Coding 人工授权状态机（不会执行代码 push）")
    p.add_argument("--repo", default=".", help="目标项目根目录")
    sub = p.add_subparsers(dest="command", required=True)
    x = sub.add_parser("init", help="初始化总计划和每一步 plan.md")
    x.add_argument("--slug", required=True); x.add_argument("--title", required=True); x.add_argument("--steps", type=int, required=True)
    x = sub.add_parser("approve-plan", help="记录用户确认了总计划及子计划")
    x.add_argument("--user-quote", required=True)
    x = sub.add_parser("allow-path", help="登记指定步骤获批的精确代码路径")
    x.add_argument("--step", type=int, required=True); x.add_argument("--path", required=True)
    x = sub.add_parser("configure-git", help="记录首次编码前的 Git 决策")
    x.add_argument("--mode", choices=["off", "per-step"], required=True)
    x.add_argument("--platform", choices=["github", "gitcode"]); x.add_argument("--remote"); x.add_argument("--branch")
    x.add_argument("--user-quote", default=""); x.add_argument("--allow-protected", action="store_true")
    x = sub.add_parser("authorize", help="记录用户明确授权当前/下一步")
    x.add_argument("--step", type=int, required=True); x.add_argument("--user-quote", required=True)
    x = sub.add_parser("verified", help="仅真实测试通过后记录结果")
    x.add_argument("--result", choices=["pass", "fail", "blocked"], required=True); x.add_argument("--evidence", required=True)
    sub.add_parser("documented", help="登记完成步骤讲解文档")
    x = sub.add_parser("revise", help="用户要求修改当前已完成/待验收步骤")
    x.add_argument("--user-quote", required=True)
    x.add_argument("--affected", nargs="*", default=[], help="受行为变化影响、需要补充确认的题号，如 Q3")
    sub.add_parser("start-precheck", help="登记必要的行为约定并锁定当前实现证据")
    x = sub.add_parser("answer-precheck", help="记录一个用户的选择，自动比较已批准方案；不进行知识评分")
    x.add_argument("--id", required=True); x.add_argument("--choice", choices=list("ABCD"), required=True)
    x.add_argument("--user-answer", required=True); x.add_argument("--summary", required=True)
    x.add_argument("--evidence", required=True)
    x.add_argument("--needs-discussion", action="store_true", help="用户虽选择当前方案但仍有保留意见")
    x = sub.add_parser("resume-precheck", help="记录用户讨论后明确保留当前约定的真实确认")
    x.add_argument("--user-quote", required=True)
    x = sub.add_parser("reset-precheck", help="用户批准后调整题库并保留未变化的确认")
    x.add_argument("--user-quote", required=True)
    x.add_argument("--affected", nargs="*", default=[], help="需要补充确认的题号")
    x = sub.add_parser("accept", help="全部预验收题通过后，用户明确正式验收本步骤")
    x.add_argument("--user-quote", required=True)
    x = sub.add_parser("pushed", help="真实成功推送后记录结果；本命令本身不 push")
    x.add_argument("--commit", required=True); x.add_argument("--success", action="store_true")
    sub.add_parser("status", help="查看活动任务状态")
    return p


def main():
    args = parser().parse_args()
    repo = Path(args.repo).expanduser().resolve()
    if not repo.is_dir():
        fail("仓库目录不存在")
    if args.command == "init":
        cmd_init(repo, args)
        return
    state = load(repo)
    handlers = {
        "approve-plan": cmd_approve_plan, "allow-path": cmd_allow_path,
        "configure-git": cmd_configure_git, "authorize": cmd_authorize,
        "verified": cmd_verified, "documented": cmd_documented,
        "start-precheck": cmd_start_precheck, "answer-precheck": cmd_answer_precheck, "resume-precheck": cmd_resume_precheck,
        "reset-precheck": cmd_reset_precheck,
        "revise": cmd_revise, "accept": cmd_accept,
        "pushed": cmd_pushed, "status": cmd_status,
    }
    handlers[args.command](repo, state, args)


if __name__ == "__main__":
    main()
