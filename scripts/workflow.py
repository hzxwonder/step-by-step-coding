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
CONFIRMATION_SOURCES = ("requirement", "delegation", "approved-plan")


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
    print("计划已批准。沿用已知保存偏好，默认 configure-git --mode off。")


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
    save(repo, state, "保存方式：" + (a.user_quote or "默认仅保留本地，未授权推送"))
    print("保存方式已记录。用户已明确授权第 1 步时可直接登记，否则先取得授权。")


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
    print("验证已记录。制作简短的 explain.md，供用户按需阅读。")


def cmd_documented(repo, state, a):
    need(state, "explaining")
    p = current_folder(repo, state) / "explain.md"
    if not p.is_file() or not p.read_text(encoding="utf-8").strip():
        fail("请先生成说明当前结果和复现方式的 explain.md")
    state["phase"] = "precheck_setup"
    save(repo, state, "当前步骤讲解文档已生成；进入预验收问题准备阶段")
    print("说明已就绪。整理关键约定并引用已有原话，只询问尚未解决的决定。")



def precheck_file(repo, state):
    return current_folder(repo, state) / "preacceptance.md"


def file_digest(path):
    if not path.is_file():
        fail("预验收问题文件缺失，禁止评分或验收")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_source_hashes(repo, state):
    """记录约定、验证与获批文件，讲解文档只检查存在。"""
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
        if file == folder / "explain.md":
            continue
        result[relative] = hashlib.sha256(file.read_bytes()).hexdigest()
    return result


def assert_source_unchanged(repo, state):
    previous = state.get("precheck", {}).get("source_hashes", {})
    explanation = (current_folder(repo, state) / "explain.md").relative_to(repo).as_posix()
    previous = {path: digest for path, digest in previous.items() if path != explanation}
    if not previous or previous != collect_source_hashes(repo, state):
        fail("本步计划、验证或获批文件已变化。请按当前授权 revise，重新核对证据并保留未变化的确认。")


def write_precheck_results(repo, state):
    """只保存真实用户的选择；不把方案偏好作为知识考试来打分。"""
    pre = state["precheck"]
    lines = [f"# 第 {state['current_step']} 步 · 需求对齐预验收记录（本地）", "",
             "> 本文档可能包含用户原话，默认不得推送 GitHub/GitCode。",
             "> 关键约定与证据见 `preacceptance.md`。",
             "> confirmed 表示按真实原话确认直接约定，D 表示仍需讨论。", ""]
    for i, rec in enumerate(pre.get("attempts", []), start=1):
        label = "已对齐" if rec["result"] == "aligned" else "需要讨论"
        lines += [f"## 第 {i} 次选择 · {rec['id']} · {label}", "",
                  f"- 用户选择：**{rec['choice']}**",
                  f"- 当前方案：**{rec['baseline']}**",
                  f"- 用户原话：{rec['user_answer']}",
                  f"- 确认来源：{rec.get('source_kind', '待补充')} · {rec.get('source_ref', '待补充')}",
                  f"- 适用范围：{rec.get('scope', '待补充')}",
                  f"- 对齐说明：{rec['summary']}",
                  f"- 需求/代码证据：{rec['evidence']}", ""]
    passed = len(pre.get("results", {}))
    lines += ["## 当前对齐状态", "", f"- 已对齐：{passed} / {len(pre['questions'])}",
              f"- 待确认：{', '.join(q for q in pre['questions'] if q not in pre['results']) or '无'}", "",
              "约定对齐后按用户明确表述记录验收。已有验收原话无需重问，下一步仍需明确授权。", ""]
    case = pre.get("case_presentation")
    lines += ["## 真实 case 展示", "",
              f"- {case['case_id']}：{case['presentation_ref']}；证据：{case['evidence']}" if case else "- 待登记当前版本的真实 case 展示", ""]
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
    if not questions:
        fail("请记录本步实际需要核对的关键约定，已有明确原话的项目无需重问")
    if questions != [f"Q{i}" for i in range(1, len(questions) + 1)]:
        fail("题号必须从 Q1 连续编号")
    baseline_map = {}
    option_map = {}
    for i, match in enumerate(headings):
        block = content[match.end():headings[i + 1].start() if i + 1 < len(headings) else len(content)]
        options = re.findall(r"(?m)^- ([ABCD])\.\s+([^\n]+)$", block)
        keys = [k for k, _ in options]
        statements = re.findall(r"(?m)^- \*\*当前约定\*\*：([^\n]*)$", block)
        for field in ("证据", "分歧处理"):
            value = re.findall(r"(?m)^- \*\*" + field + r"\*\*：([^\n]*)$", block)
            if len(value) != 1 or not value[0].strip():
                fail(f"{questions[i]} 缺少具体的{field}")
        if statements:
            if len(statements) != 1 or not statements[0].strip() or keys or "**当前约定选项**" in block:
                fail(f"{questions[i]} 应只写一条明确的当前约定，不与选项混写")
            baseline_map[questions[i]] = "confirmed"
            option_map[questions[i]] = ["confirmed", "D"]
            continue
        if keys not in (["A", "B", "D"], ["A", "B", "C", "D"]):
            fail(f"{questions[i]} 请直接记录当前约定，或提供实际行为选项及 D 讨论出口")
        labels = [v.strip() for _, v in options]
        if any(len(v) < 3 for v in labels) or len(set(labels)) != len(labels):
            fail(f"{questions[i]} 选项必须具体、不重复，且不能为空")
        if not any(t in labels[-1] for t in ("其他", "不确定", "需要讨论", "不符合")):
            fail(f"{questions[i]} 的 D 选项必须允许用户表达不确定、其他期望或需要讨论")
        baseline = re.findall(r"(?m)^- \*\*当前约定选项\*\*：([ABCD])\s*$", block)
        if len(baseline) != 1 or baseline[0] not in keys[:-1]:
            fail(f"{questions[i]} 的当前约定必须对应一个实际提供的行为选项")
        baseline_map[questions[i]] = baseline[0]
        option_map[questions[i]] = keys
    return questions, baseline_map, option_map


def decision_levels(path):
    blocks = re.split(r"(?m)(?=^### Q[1-9][0-9]*\s)", path.read_text(encoding="utf-8"))[1:]
    levels = {}
    for block in blocks:
        qid = re.match(r"### (Q[1-9][0-9]*)", block).group(1)
        level = re.findall(r"(?m)^- \*\*决策层级\*\*：(核心|体验)\s*$", block)
        impact = re.findall(r"(?m)^- \*\*选择影响\*\*：([^\n]+)$", block)
        if len(level) != 1 or len(impact) != 1 or not impact[0].strip():
            fail(f"{qid} 请写明决策层级与选择影响，先识别核心未决项")
        levels[qid] = level[0]
    return levels


def pending_questions(pre):
    pending = [q for q in pre["questions"] if q not in pre["results"]]
    return sorted(pending, key=lambda q: pre.get("levels", {}).get(q) != "核心")


def has_confirmation_source(record):
    return (record.get("source_kind") in CONFIRMATION_SOURCES
            and bool(record.get("source_ref", "").strip())
            and bool(record.get("scope", "").strip()))


def question_hashes(path):
    """逐项比较行为约定；证据与讨论说明更新不撤销用户选择。"""
    content = path.read_text(encoding="utf-8")
    blocks = re.split(r"(?m)(?=^### Q[1-9][0-9]*\s)", content)[1:]
    hashes = {}
    for block in blocks:
        head, _, tail = block.partition("- **证据**")
        behavior = head.strip()
        trailing_fields = re.findall(r"(?m)^- (?:[ABCD]\.\s+|\*\*当前约定(?:选项)?\*\*：)[^\n]*$", tail)
        if trailing_fields:
            behavior += "\n" + "\n".join(trailing_fields)
        qid = re.match(r"### (Q[1-9][0-9]*)", block).group(1)
        hashes[qid] = hashlib.sha256(behavior.encode()).hexdigest()
    return hashes


def invalidate_affected(repo, state, affected):
    pre = state["precheck"]
    if any(q not in pre["questions"] for q in affected):
        fail("受影响题号必须属于当前步骤约定清单")
    if pre["questions"] and precheck_file(repo, state).is_file() and not pre.get("question_hashes") and pre.get("file_hash") == file_digest(precheck_file(repo, state)):
        pre["question_hashes"] = question_hashes(precheck_file(repo, state))
    for q in affected:
        pre["results"].pop(q, None)


def cmd_start_precheck(repo, state, a):
    need(state, "precheck_setup")
    path = precheck_file(repo, state)
    questions, baselines, options = validate_question_file(path)
    levels = decision_levels(path)
    hashes = question_hashes(path)
    previous = state.get("precheck") or empty_precheck()
    old_hashes = previous.get("question_hashes", {})
    same_file = previous.get("file_hash") == file_digest(path)
    retained = {q: record for q, record in previous["results"].items()
                if q in questions and record.get("result") == "aligned" and has_confirmation_source(record)
                and record.get("choice") == baselines[q]
                and (old_hashes.get(q) == hashes[q] or (not old_hashes and same_file))}
    state["precheck"] = {"schema": PRECHECK_SCHEMA, "questions": questions, "baselines": baselines,
                         "options": options, "levels": levels,
                         "results": retained, "attempts": previous["attempts"],
                         "question_hashes": hashes, "file_hash": file_digest(path),
                         "source_hashes": collect_source_hashes(repo, state)}
    if (previous.get("case_presentation") and old_hashes == hashes
            and previous.get("source_hashes") == state["precheck"]["source_hashes"]):
        state["precheck"]["case_presentation"] = previous["case_presentation"]
    pending = pending_questions(state["precheck"])
    state["phase"] = "precheck" if pending else "await_acceptance"
    write_precheck_results(repo, state)
    save(repo, state, f"当前约定已锁定；保留 {len(retained)} 项确认，待确认 {len(pending)} 项")
    print(f"为 {pending[0]} 引用已有原话或解决待定项。" if pending else "已有确认均适用。核对真实 case 展示记录后登记验收。")


def cmd_answer_precheck(repo, state, a):
    need(state, "precheck")
    pre = state.get("precheck") or {}
    if pre.get("schema") != PRECHECK_SCHEMA:
        fail("当前记录格式不受支持。请按已有需求原话 reset-precheck，再整理关键约定。")
    if pre.get("file_hash") != file_digest(precheck_file(repo, state)):
        fail("当前约定已变更。请按对应要求 reset-precheck，只补充变化的确认。")
    assert_source_unchanged(repo, state)
    remaining = [x for x in pre["questions"] if x not in pre["results"]]
    if a.id not in remaining:
        fail("该约定不存在或已经确认，请检查记录对象")
    baseline = pre["baselines"].get(a.id)
    choice = a.choice or ("confirmed" if baseline == "confirmed" else None)
    if choice not in pre.get("options", {}).get(a.id, list("ABCD")):
        fail("该确认项未提供这个选项；请保留用户原话，先澄清实际期望")
    for field in ("user_answer", "summary", "evidence", "source_ref", "scope"):
        if not getattr(a, field, "").strip():
            fail("请记录真实原话、来源位置、适用范围、对齐说明与实现证据")
    if a.source_kind not in CONFIRMATION_SOURCES + ("discussion",):
        fail("启动授权和 Agent 自选方案不能确认需求。请引用明确要求、明确委托或已批准的具体约定。")
    if baseline not in ("A", "B", "C", "confirmed"):
        fail("当前约定选项无效，不能自动对齐")
    aligned = choice == baseline and not a.needs_discussion and a.source_kind in CONFIRMATION_SOURCES
    record = {"id": a.id, "choice": choice, "baseline": baseline,
              "result": "aligned" if aligned else "discussion",
              "user_answer": a.user_answer, "summary": a.summary, "evidence": a.evidence,
              "source_kind": a.source_kind, "source_ref": a.source_ref, "scope": a.scope}
    pre["attempts"].append(record)
    if aligned:
        pre["results"][a.id] = record
        state["phase"] = "await_acceptance" if len(pre["results"]) == len(pre["questions"]) else "precheck"
    else:
        state["phase"] = "precheck_discussion"
    write_precheck_results(repo, state)
    save(repo, state, f"记录约定 {a.id}：{choice}；当前约定 {baseline}；{record['result']}")
    if not aligned:
        print("出现需求分歧或不确定：这不是答错。暂停后续问题，解释当前方案、代码和差别；用户明确决定保留则 resume-precheck 记录该次确认，决定修改则 revise 后重新验证。")
    elif state["phase"] == "await_acceptance":
        print("关键约定已对齐。展示或引用当前真实 case 后，按用户原话登记验收，只询问仍缺的决定。")
    else:
        upcoming = pending_questions(pre)[0]
        print(f"本项已对齐，接着记录 {upcoming}。只向用户询问仍未解决的决定。")


def cmd_resume_precheck(repo, state, a):
    need(state, "precheck_discussion")
    if not a.user_quote.strip() or not a.source_ref.strip():
        fail("请记录用户解决分歧的原话及消息位置")
    if state.get("precheck", {}).get("file_hash") != file_digest(precheck_file(repo, state)):
        fail("约定清单发生变化，必须重设预验收")
    assert_source_unchanged(repo, state)
    state["phase"] = "precheck"
    pre = state["precheck"]
    q = pre["attempts"][-1]["id"]
    cmd_answer_precheck(repo, state, argparse.Namespace(
        id=q, choice=pre["baselines"][q], user_answer=a.user_quote,
        summary="用户讨论后明确确认当前行为", evidence=pre["attempts"][-1]["evidence"],
        source_kind="requirement", source_ref=a.source_ref, scope=pre["attempts"][-1]["scope"],
        needs_discussion=False))


def cmd_present_case(repo, state, a):
    need(state, "precheck", "precheck_discussion", "await_acceptance")
    assert_source_unchanged(repo, state)
    if a.kind != "real":
        fail("正常验收需要真实 case。模拟或未运行状态请记录限制，不能登记为已展示的真实运行。")
    for field in ("case_id", "evidence", "presentation_ref", "summary"):
        if not getattr(a, field, "").strip():
            fail("请记录真实 case、运行证据、展示位置和输入到结果的说明")
    path = (repo / a.evidence).resolve()
    if not path.is_relative_to(repo) or not path.is_file() or not path.read_bytes().strip():
        fail("运行证据须为当前项目内实际存在且非空的文件")
    state["precheck"]["case_presentation"] = {
        "case_id": a.case_id, "kind": a.kind, "evidence": path.relative_to(repo).as_posix(),
        "evidence_sha256": file_digest(path), "presentation_ref": a.presentation_ref, "summary": a.summary}
    write_precheck_results(repo, state)
    save(repo, state, "已展示真实 case：" + a.case_id + "；位置：" + a.presentation_ref)
    print("真实 case 展示已记录。只询问尚未明确的核心决定，不重复已有确认。")


def cmd_reset_precheck(repo, state, a):
    need(state, "precheck", "precheck_discussion", "await_acceptance", "precheck_setup")
    if not a.user_quote.strip():
        fail("请记录适用于本次整理或变化的真实要求、授权或澄清原话")
    invalidate_affected(repo, state, a.affected)
    state["phase"] = "precheck_setup"
    save(repo, state, "调整约定清单，保留未变化的确认：" + a.user_quote)
    print("修改问题后执行 start-precheck；只补充变化或尚未解决的项目。")


def cmd_revise(repo, state, a):
    need(state, "precheck_setup", "precheck", "precheck_discussion", "await_acceptance", "explaining", "await_next_step", "completed")
    if not a.user_quote.strip():
        fail("请记录本次修订所依据的当前步骤授权或需求变化原话")
    invalidate_affected(repo, state, a.affected)
    if state["current_step"] in state["accepted_steps"]:
        state["accepted_steps"].remove(state["current_step"])
    state["phase"] = "implementing"
    state["precheck"].pop("case_presentation", None)
    save(repo, state, "按当前授权修订，重验受影响实现并保留未变化的确认：" + a.user_quote)
    print("修改后验证受影响实现、更新讲解；只确认新增、变化或尚未解决的行为。")


def cmd_accept(repo, state, a):
    need(state, "await_acceptance")
    pre = state.get("precheck", {})
    qs = pre.get("questions", [])
    passed = pre.get("results", {})
    if pre.get("schema") != PRECHECK_SCHEMA or not qs or any(
            passed.get(q, {}).get("result") != "aligned" or not has_confirmation_source(passed[q]) for q in qs):
        fail("关键约定尚未都有真实确认与证据，不能验收")
    if pre.get("file_hash") != file_digest(precheck_file(repo, state)):
        fail("预验收约定清单被修改，需重设并重新逐项预验收")
    assert_source_unchanged(repo, state)
    case = pre.get("case_presentation")
    if not case or file_digest(repo / case["evidence"]) != case["evidence_sha256"]:
        fail("验收前请展示并登记当前版本的真实 case，包含关键实现、日志、输出与结论依据")
    if not a.user_quote.strip():
        fail("必须记录用户明确验收通过的原话")
    if state["current_step"] not in state["accepted_steps"]:
        state["accepted_steps"].append(state["current_step"])
    state["phase"] = "await_push" if state["git"]["mode"] == "per-step" else next_phase(state)
    save(repo, state, f"用户明确验收步骤 {state['current_step']}：{a.user_quote}")
    print("本步已验收。" + ("按已确认目标 push 并记录结果。" if state["phase"] == "await_push" else "只有已明确授权下一步时才继续。"))


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
    x = sub.add_parser("revise", help="根据当前授权修订本步骤，重新核对受影响证据")
    x.add_argument("--user-quote", required=True)
    x.add_argument("--affected", nargs="*", default=[], help="受行为变化影响、需要补充确认的题号，如 Q3")
    sub.add_parser("start-precheck", help="登记必要的行为约定并锁定当前实现证据")
    x = sub.add_parser("answer-precheck", help="按用户真实原话记录直接约定或选项")
    x.add_argument("--id", required=True); x.add_argument("--choice", choices=list("ABCD") + ["confirmed"])
    x.add_argument("--user-answer", required=True); x.add_argument("--summary", required=True)
    x.add_argument("--evidence", required=True)
    x.add_argument("--source-kind", choices=list(CONFIRMATION_SOURCES) + ["discussion", "authorization", "agent-choice"], required=True)
    x.add_argument("--source-ref", required=True, help="原话所在消息或已批准具体约定的位置")
    x.add_argument("--scope", required=True, help="原话实际覆盖的行为与适用条件")
    x.add_argument("--needs-discussion", action="store_true", help="用户虽选择当前方案但仍有保留意见")
    x = sub.add_parser("resume-precheck", help="记录用户讨论后明确保留当前约定的真实确认")
    x.add_argument("--user-quote", required=True)
    x.add_argument("--source-ref", required=True)
    x = sub.add_parser("present-case", help="登记已向用户展示的真实运行及关键依据")
    x.add_argument("--case-id", required=True); x.add_argument("--kind", choices=["real", "simulated", "not-run"], required=True)
    x.add_argument("--evidence", required=True); x.add_argument("--presentation-ref", required=True)
    x.add_argument("--summary", required=True, help="已展示的输入、关键实现、日志、输出与结论依据")
    x = sub.add_parser("reset-precheck", help="按对应要求整理约定，保留未变化的确认")
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
        "present-case": cmd_present_case,
        "reset-precheck": cmd_reset_precheck,
        "revise": cmd_revise, "accept": cmd_accept,
        "pushed": cmd_pushed, "status": cmd_status,
    }
    handlers[args.command](repo, state, args)


if __name__ == "__main__":
    main()
