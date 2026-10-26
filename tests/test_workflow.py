import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
CLI = SKILL / "scripts" / "workflow.py"
spec = importlib.util.spec_from_file_location("guard_edit", SKILL / "scripts" / "guard_edit.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class WorkflowTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name).resolve()
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.repo, check=True)
        (self.repo / "README.md").write_text("test\n")
        subprocess.run(["git", "add", "README.md"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=self.repo, check=True)

    def call(self, *args, succeeds=True):
        cmd = [sys.executable, str(CLI), "--repo", str(self.repo), *args]
        r = subprocess.run(cmd, text=True, capture_output=True)
        if succeeds:
            self.assertEqual(r.returncode, 0, r.stdout + "\n" + r.stderr)
        else:
            self.assertNotEqual(r.returncode, 0, "expected failure: " + str(args))
        return r

    def read_state(self):
        return json.loads((self.repo / ".ai-collab" / "demo" / "state.json").read_text())

    def fill_plan_rationale(self, steps):
        """模拟用户和 Agent 已填写真实的步骤必要性与全局作用。"""
        master = self.repo / "docs" / "ai-collab" / "demo" / "plan.md"
        content = master.read_text(encoding="utf-8")
        lines = []
        for line in content.splitlines():
            if line.startswith("| 01 |") or line.startswith("| 02 |"):
                continue  # 删除 CLI 生成的两条尚未完成的占位行
            lines.append(line)
        for n in range(1, steps + 1):
            lines.append(f"| {n:02d} | 形成第{n}步核心能力 | 当前用户缺少第{n}步能力，无法完成完整业务流程 | 本步为项目提供可被下一阶段复用的功能和接口 | 能独立调用接口并观察输出 | 连接前后步骤 | 未授权 |")
        master.write_text("\n".join(lines) + "\n", encoding="utf-8")
        for n in range(1, steps + 1):
            p = self.repo / "docs" / "ai-collab" / "demo" / "steps" / f"{n:02d}-step" / "plan.md"
            text = p.read_text(encoding="utf-8")
            reasons = {
                "当前问题": f"用户缺少第{n}步基础能力，目前的项目无法完成这一部分业务流程",
                "不做的后果": "如果直接跳过这一步，后续功能缺少必要的数据来源和独立接口",
                "安排在此时的原因": "先获得能够独立验证的基本能力，之后才能安全扩展后续功能",
                "对总目标的贡献": "提供总任务要求的基础业务能力，使完整用户使用流程能够成立",
                "承接什么": "从已有项目入口承接用户输入，第一步建立基础功能，以后复用前一步成果",
                "为后续提供什么": "形成稳定输入输出接口，供后续页面和业务规则直接调用",
                "可验证的阶段成果": "通过独立测试验证当前接口成功处理一条模拟用户请求",
            }
            for key, value in reasons.items():
                text = re.sub(r"(?m)^- \*\*" + re.escape(key) + r"\*\*：.*$", f"- **{key}**：{value}", text)
            p.write_text(text, encoding="utf-8")

    def init_plan(self, steps=2):
        self.call("init", "--slug", "demo", "--title", "示范", "--steps", str(steps))
        self.fill_plan_rationale(steps)
        self.call("allow-path", "--step", "1", "--path", "src/one.py")
        self.call("allow-path", "--step", "2", "--path", "src/two.py") if steps > 1 else None
        self.call("approve-plan", "--user-quote", "我认可两个计划")

    def prepare_docs(self, step, choices=("A", "B", "C", "A"), two_options=False):
        folder = self.repo / "docs" / "ai-collab" / "demo" / "steps" / f"{step:02d}-step"
        (folder / "verification.md").write_text("# 验证\n命令: python -m pytest; exit code 0; 通过。\n")
        (folder / "explain.md").write_text("# 代码讲解\n" + "解释真实输入、输出及边界条件和如何验证。" * 20)
        folder_source = self.repo / "src"
        folder_source.mkdir(exist_ok=True)
        (folder_source / ("one.py" if step == 1 else "two.py")).write_text("def feature():\n    return 'ready'\n")
        options = ("- A. 输入合法时展示新增结果\n"
                   "- B. 输入合法后仅显示提示\n"
                   + ("" if two_options else "- C. 输入合法后直接返回首页\n")
                   + "- D. 其他 / 不确定 / 想先讨论\n")
        (folder / "preacceptance.md").write_text("# 预验收\n" + "\n".join(
            f"### Q{i} 你希望这一步采用哪种行为？\n" + options
            + f"- **当前约定选项**：{choice}\n"
            + "- **证据**：src/one.py 与当前步骤 plan.md\n"
            + "- **分歧处理**：讨论是否改变当前步骤范围\n"
            for i, choice in enumerate(choices, 1)
        ), encoding="utf8")

    def aligned_answer(self, i):
        choices = ["A", "B", "C", "A"]
        self.call("answer-precheck", "--id", f"Q{i}", "--choice", choices[i-1],
                  "--user-answer", f"我选择{choices[i-1]}，这是我要的行为",
                  "--summary", "用户确认现行功能，与代码和步骤计划一致",
                  "--evidence", f"steps/0{self.read_state()['current_step']}-step/plan.md + src/one.py")

    def pass_precheck(self):
        self.call("start-precheck")
        for i in range(1, 5):
            self.aligned_answer(i)

    def test_missing_rationale_blocks_plan_approval(self):
        self.call("init", "--slug", "demo", "--title", "示范", "--steps", "1")
        self.call("approve-plan", "--user-quote", "批准", succeeds=False)
        self.fill_plan_rationale(1)
        step = self.repo / "docs/ai-collab/demo/steps/01-step/plan.md"
        step.write_text(step.read_text().replace("**不做的后果**：如果直接跳过这一步，后续功能缺少必要的数据来源和独立接口", "**不做的后果**："))
        self.call("approve-plan", "--user-quote", "批准", succeeds=False)
        self.fill_plan_rationale(1)
        self.call("approve-plan", "--user-quote", "我认可这一步的必要性与项目作用")
        self.assertEqual(self.read_state()["phase"], "await_git_preference")

    def test_master_step_role_required(self):
        self.call("init", "--slug", "demo", "--title", "示范", "--steps", "1")
        self.fill_plan_rationale(1)
        master = self.repo / "docs/ai-collab/demo/plan.md"
        master.write_text(master.read_text().replace("本步为项目提供可被下一阶段复用的功能和接口", "待讨论"))
        self.call("approve-plan", "--user-quote", "我批准", succeeds=False)

    def test_rationale_must_remain_valid_before_authorize(self):
        self.init_plan(steps=1)
        self.call("configure-git", "--mode", "off", "--user-quote", "本地")
        step = self.repo / "docs/ai-collab/demo/steps/01-step/plan.md"
        step.write_text(step.read_text().replace("**对总目标的贡献**：提供总任务要求的基础业务能力，使完整用户使用流程能够成立", "**对总目标的贡献**："))
        self.call("authorize", "--step", "1", "--user-quote", "开始", succeeds=False)
        self.fill_plan_rationale(1)
        self.call("authorize", "--step", "1", "--user-quote", "开始第1步")

    def test_user_must_authorize_each_step_separately(self):
        self.init_plan()
        self.call("authorize", "--step", "1", "--user-quote", "开始第1步", succeeds=False)
        self.call("configure-git", "--mode", "off", "--user-quote", "本地保存")
        self.call("authorize", "--step", "1", "--user-quote", "开始第1步")
        self.call("authorize", "--step", "2", "--user-quote", "开始第2步", succeeds=False)
        self.call("accept", "--user-quote", "本步骤验收通过", succeeds=False)
        self.call("verified", "--result", "pass", "--evidence", "通过", succeeds=False)
        self.prepare_docs(1)
        self.call("verified", "--result", "fail", "--evidence", "测试失败", succeeds=False)
        self.call("verified", "--result", "pass", "--evidence", "pytest exit 0")
        self.call("accept", "--user-quote", "本步骤验收通过", succeeds=False)
        self.call("documented")
        self.call("accept", "--user-quote", "本步骤验收通过", succeeds=False)
        self.pass_precheck()
        self.call("accept", "--user-quote", "本步骤验收通过")
        self.assertEqual(self.read_state()["phase"], "await_next_step")
        self.call("authorize", "--step", "2", "--user-quote", "现在开始第2步")
        self.assertEqual(self.read_state()["phase"], "implementing")
        self.assertEqual(self.read_state()["current_step"], 2)

    def test_push_wait_and_no_skip(self):
        self.init_plan(steps=1)
        subprocess.run(["git", "remote", "add", "origin", "https://example.invalid/demo.git"], cwd=self.repo, check=True)
        self.call("configure-git", "--mode", "per-step", "--platform", "github", "--remote", "origin", "--branch", "main", "--user-quote", "我批准", succeeds=False)
        self.call("configure-git", "--mode", "per-step", "--platform", "github", "--remote", "origin", "--branch", "feature/demo", "--user-quote", "我选择 GitHub")
        self.call("authorize", "--step", "1", "--user-quote", "开始第一步")
        self.prepare_docs(1)
        self.call("verified", "--result", "pass", "--evidence", "pytest exit=0")
        self.call("documented")
        self.pass_precheck()
        self.call("accept", "--user-quote", "本步验收通过")
        self.assertEqual(self.read_state()["phase"], "await_push")
        self.call("pushed", "--commit", "fake", "--success", succeeds=False)
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo, text=True, capture_output=True, check=True).stdout.strip()
        self.call("pushed", "--commit", sha, "--success")
        self.assertEqual(self.read_state()["phase"], "completed")

    def test_guard_blocks_future_code(self):
        self.call("init", "--slug", "demo", "--title", "示范", "--steps", "2")
        self.fill_plan_rationale(2)
        self.call("allow-path", "--step", "1", "--path", "src/one.py")
        self.call("allow-path", "--step", "2", "--path", "src/two.py")
        def check(path):
            return guard.check({"tool_name": "Write", "tool_input": {"file_path": str(self.repo / path)}}, self.repo)
        self.assertIsNotNone(check("src/one.py"))
        self.assertIsNone(check("docs/ai-collab/demo/steps/02-step/plan.md"))
        self.call("approve-plan", "--user-quote", "我批准了这两步计划")
        self.call("configure-git", "--mode", "off")
        self.call("authorize", "--step", "1", "--user-quote", "开始第一步")
        self.assertIsNone(check("src/one.py"))
        self.assertIsNotNone(check("src/two.py"))
        self.assertIsNotNone(check(".ai-collab/demo/state.json"))
        self.assertIsNotNone(check("../escape.py"))
        self.assertIsNotNone(check(".env"))
        self.prepare_docs(1)
        self.call("verified", "--result", "pass", "--evidence", "pytest pass")
        self.assertIsNotNone(check("src/one.py"))
        self.assertIsNone(check("docs/ai-collab/demo/steps/01-step/explain.md"))
        self.call("documented")
        self.assertIsNone(check("docs/ai-collab/demo/steps/01-step/preacceptance.md"))
        self.call("start-precheck")
        self.assertIsNotNone(check("docs/ai-collab/demo/steps/01-step/preacceptance.md"))
        self.assertIsNotNone(check("src/one.py"))

    def test_revise_requires_reverify(self):
        self.init_plan(steps=1)
        self.call("configure-git", "--mode", "off")
        self.call("authorize", "--step", "1", "--user-quote", "开始第一步")
        self.prepare_docs(1)
        self.call("verified", "--result", "pass", "--evidence", "pytest pass")
        self.call("documented")
        self.pass_precheck()
        self.call("accept", "--user-quote", "验收通过")
        self.call("revise", "--user-quote", "我想修改这个步骤")
        self.assertEqual(self.read_state()["phase"], "implementing")
        self.assertEqual(self.read_state()["accepted_steps"], [])


    def test_precheck_blocks_skip_and_requires_all_questions(self):
        self.init_plan(steps=1)
        self.call("configure-git", "--mode", "off")
        self.call("authorize", "--step", "1", "--user-quote", "开始第一步")
        self.prepare_docs(1)
        self.call("verified", "--result", "pass", "--evidence", "pytest exit 0")
        self.call("documented")
        self.call("accept", "--user-quote", "我懂了", succeeds=False)
        self.call("answer-precheck", "--id", "Q1", "--choice", "A", "--user-answer", "A", "--summary", "同意", "--evidence", "plan.md", succeeds=False)
        self.call("start-precheck")
        self.call("answer-precheck", "--id", "Q2", "--choice", "B", "--user-answer", "B", "--summary", "同意", "--evidence", "plan.md", succeeds=False)
        self.aligned_answer(1)
        self.call("accept", "--user-quote", "验收通过", succeeds=False)
        self.assertEqual(self.read_state()["precheck"]["results"]["Q1"]["result"], "aligned")
        for i in range(2, 5):
            self.aligned_answer(i)
        self.assertEqual(self.read_state()["phase"], "await_acceptance")
        self.call("accept", "--user-quote", "本步骤验收通过")
        self.assertEqual(self.read_state()["phase"], "completed")

    def test_different_preference_is_a_discussion_not_wrong_answer(self):
        self.init_plan(steps=1)
        self.call("configure-git", "--mode", "off")
        self.call("authorize", "--step", "1", "--user-quote", "开始第一步")
        self.prepare_docs(1)
        self.call("verified", "--result", "pass", "--evidence", "pytest exit 0")
        self.call("documented")
        self.call("start-precheck")
        self.call("answer-precheck", "--id", "Q1", "--choice", "B",
                  "--user-answer", "我希望只弹出提示", "--summary", "用户期望与当前已实现行为不同",
                  "--evidence", "plan.md + src/one.py")
        self.assertEqual(self.read_state()["phase"], "precheck_discussion")
        self.assertEqual(self.read_state()["precheck"]["results"], {})
        self.call("answer-precheck", "--id", "Q2", "--choice", "B", "--user-answer", "B", "--summary", "同意", "--evidence", "plan.md", succeeds=False)
        self.call("accept", "--user-quote", "已经验收", succeeds=False)
        self.call("resume-precheck", "--user-quote", "听了说明，我决定保留目前方案")
        self.assertEqual(self.read_state()["phase"], "precheck")
        self.assertEqual(list(self.read_state()["precheck"]["results"]), ["Q1"])
        for i in range(2, 5):
            self.aligned_answer(i)
        self.call("accept", "--user-quote", "正式验收")

    def test_other_or_uncertain_blocks_until_discussion_then_revision(self):
        self.init_plan(steps=1)
        self.call("configure-git", "--mode", "off")
        self.call("authorize", "--step", "1", "--user-quote", "开始第一步")
        self.prepare_docs(1)
        self.call("verified", "--result", "pass", "--evidence", "pytest exit 0")
        self.call("documented")
        self.call("start-precheck")
        self.call("answer-precheck", "--id", "Q1", "--choice", "D", "--user-answer", "不确定，我想先看看实际界面", "--summary", "需要实例",
                  "--evidence", "当前步骤 plan.md")
        self.assertEqual(self.read_state()["phase"], "precheck_discussion")
        self.call("revise", "--user-quote", "讨论后我决定更改功能")
        self.assertEqual(self.read_state()["phase"], "implementing")
        self.assertEqual(self.read_state()["precheck"]["results"], {})

    def test_agreement_with_reservation_still_requires_discussion(self):
        self.init_plan(steps=1)
        self.call("configure-git", "--mode", "off")
        self.call("authorize", "--step", "1", "--user-quote", "开始第一步")
        self.prepare_docs(1)
        self.call("verified", "--result", "pass", "--evidence", "pytest exit 0")
        self.call("documented")
        self.call("start-precheck")
        self.call("answer-precheck", "--id", "Q1", "--choice", "A", "--needs-discussion",
                  "--user-answer", "选A，但我对保存时机还有疑问", "--summary", "仍有需要澄清的行为",
                  "--evidence", "步骤计划和真实代码")
        self.assertEqual(self.read_state()["phase"], "precheck_discussion")

    def test_evidence_updates_and_revision_preserve_confirmations(self):
        self.init_plan(steps=1)
        self.call("configure-git", "--mode", "off")
        self.call("authorize", "--step", "1", "--user-quote", "开始第一步")
        self.prepare_docs(1)
        self.call("verified", "--result", "pass", "--evidence", "pytest exit 0")
        self.call("documented")
        self.call("start-precheck")
        self.aligned_answer(1)
        file = self.repo / "docs/ai-collab/demo/steps/01-step/preacceptance.md"
        file.write_text(file.read_text() + "\n新增不一样的说明\n")
        self.call("answer-precheck", "--id", "Q2", "--choice", "B", "--user-answer", "我选择B", "--summary", "同意", "--evidence", "src/one.py", succeeds=False)
        self.call("reset-precheck", "--user-quote", "题目有歧义，同意重新开始")
        self.call("start-precheck")
        self.assertEqual(list(self.read_state()["precheck"]["results"]), ["Q1"])
        self.call("revise", "--user-quote", "本步骤需求要改变", "--affected", "Q3")
        self.assertEqual(self.read_state()["phase"], "implementing")
        self.assertEqual(list(self.read_state()["precheck"]["results"]), ["Q1"])
        self.call("accept", "--user-quote", "验收通过", succeeds=False)

    def test_precheck_rejects_placeholder_and_knowledge_qa(self):
        self.init_plan(steps=1)
        self.call("configure-git", "--mode", "off")
        self.call("authorize", "--step", "1", "--user-quote", "开始第一步")
        self.prepare_docs(1)
        self.call("verified", "--result", "pass", "--evidence", "pytest exit 0")
        self.call("documented")
        path = self.repo / "docs/ai-collab/demo/steps/01-step/preacceptance.md"
        path.write_text('### Q1 <填写问题>\n- A. 选项\n- B. 选项\n- C. 选项\n- D. 其他 / 不确定\n- **当前约定选项**：A\n- **证据**：源码\n- **分歧处理**：讨论')
        self.call("start-precheck", succeeds=False)
        path.write_text('\n'.join(f'### Q{i} 哪个函数负责？\n- **必须答到**：1;2\n- **证据**：真实代码\n- **补救阅读**：详细文档' for i in range(1, 5)))
        self.call("start-precheck", succeeds=False)
        self.prepare_docs(1)
        path.write_text(path.read_text().replace("- **当前约定选项**：C", "- **当前约定选项**：D"))
        self.call("start-precheck", succeeds=False)

    def test_code_changes_after_questions_locked_block_acceptance(self):
        self.init_plan(steps=1)
        self.call("configure-git", "--mode", "off")
        self.call("authorize", "--step", "1", "--user-quote", "开始第一步")
        self.prepare_docs(1)
        self.call("verified", "--result", "pass", "--evidence", "pytest exit 0")
        self.call("documented")
        self.call("start-precheck")
        self.aligned_answer(1)
        source = self.repo / "src" / "one.py"
        source.write_text(source.read_text() + "\n# stealth change\n")
        self.call("answer-precheck", "--id", "Q2", "--choice", "B", "--user-answer", "B", "--summary", "同意", "--evidence", "plan.md", succeeds=False)
        self.call("revise", "--user-quote", "代码有修改需要重新验证")
        self.assertEqual(self.read_state()["phase"], "implementing")



    def test_revision_before_question_setup(self):
        self.init_plan(steps=1)
        self.call("configure-git", "--mode", "off")
        self.call("authorize", "--step", "1", "--user-quote", "开始第一步")
        self.prepare_docs(1)
        self.call("verified", "--result", "pass", "--evidence", "测试通过")
        (self.repo / "docs/ai-collab/demo/steps/01-step/preacceptance.md").unlink()
        self.call("revise", "--user-quote", "补充当前步骤")
        self.assertEqual(self.read_state()["phase"], "implementing")

    def test_partial_revision_keeps_other_confirmations_and_source_guard(self):
        self.init_plan(steps=2)
        self.call("configure-git", "--mode", "off")
        self.call("authorize", "--step", "1", "--user-quote", "开始第一步")
        self.prepare_docs(1)
        self.call("verified", "--result", "pass", "--evidence", "测试通过")
        self.call("documented")
        self.pass_precheck()
        self.call("revise", "--user-quote", "修改保存规则", "--affected", "Q3")
        self.assertEqual(set(self.read_state()["precheck"]["results"]), {"Q1", "Q2", "Q4"})
        self.call("verified", "--result", "pass", "--evidence", "保存测试通过")
        self.call("documented")
        self.call("start-precheck")
        self.assertEqual(set(self.read_state()["precheck"]["results"]), {"Q1", "Q2", "Q4"})
        self.call("accept", "--user-quote", "通过", succeeds=False)
        self.aligned_answer(3)
        self.assertEqual(self.read_state()["phase"], "await_acceptance")
        self.call("accept", "--user-quote", "正式验收")
        self.call("authorize", "--step", "2", "--user-quote", "开始第二步")
        self.assertEqual(self.read_state()["precheck"]["results"], {})

    def test_changed_question_invalidates_only_its_confirmation(self):
        self.init_plan(steps=1)
        self.call("configure-git", "--mode", "off")
        self.call("authorize", "--step", "1", "--user-quote", "开始第一步")
        self.prepare_docs(1)
        self.call("verified", "--result", "pass", "--evidence", "测试通过")
        self.call("documented")
        self.pass_precheck()
        self.call("reset-precheck", "--user-quote", "修改第三项行为描述")
        p = self.repo / "docs/ai-collab/demo/steps/01-step/preacceptance.md"
        p.write_text(p.read_text().replace("### Q3 你希望这一步采用哪种行为？", "### Q3 保存时希望采用哪种行为？"))
        self.call("start-precheck")
        self.assertEqual(set(self.read_state()["precheck"]["results"]), {"Q1", "Q2", "Q4"})
        self.aligned_answer(3)

    def test_mutable_answer_log_does_not_invalidate_source(self):
        self.init_plan(steps=1)
        self.call("allow-path", "--step", "1", "--path", "docs/ai-collab/demo/steps/01-step/preacceptance-results.md")
        self.call("configure-git", "--mode", "off")
        self.call("authorize", "--step", "1", "--user-quote", "开始第一步")
        self.prepare_docs(1)
        self.call("verified", "--result", "pass", "--evidence", "测试通过")
        self.call("documented")
        self.pass_precheck()
        self.call("reset-precheck", "--user-quote", "更新证据说明")
        self.call("start-precheck")
        self.assertEqual(self.read_state()["phase"], "await_acceptance")
        self.call("accept", "--user-quote", "正式验收")

    def test_existing_confirmation_state_resumes_without_new_options_field(self):
        self.init_plan(steps=1)
        self.call("configure-git", "--mode", "off")
        self.call("authorize", "--step", "1", "--user-quote", "开始第一步")
        self.prepare_docs(1)
        self.call("verified", "--result", "pass", "--evidence", "功能测试通过")
        self.call("documented")
        self.call("start-precheck")
        self.aligned_answer(1)
        state = self.read_state()
        state["precheck"].pop("options")
        path = self.repo / ".ai-collab/demo/state.json"
        path.write_text(json.dumps(state, ensure_ascii=False))
        for i in range(2, 5):
            self.aligned_answer(i)
        self.assertEqual(len(self.read_state()["precheck"]["results"]), 4)
        self.call("accept", "--user-quote", "这部分符合预期")
        self.assertEqual(self.read_state()["phase"], "completed")

    def test_natural_replies_and_two_options_keep_step_authorization_separate(self):
        self.init_plan(steps=2)
        self.call("configure-git", "--mode", "off")
        self.call("authorize", "--step", "1", "--user-quote", "先做刚才确定的第一步")
        self.prepare_docs(1, choices=("A", "B"), two_options=True)
        self.call("verified", "--result", "pass", "--evidence", "功能测试通过")
        self.call("documented")
        self.call("start-precheck")
        for q, choice, quote in [("Q1", "A", "保存后就让我看到新记录"),
                                  ("Q2", "B", "这里只提醒我保存好了就行")]:
            self.call("answer-precheck", "--id", q, "--choice", choice,
                      "--user-answer", quote, "--summary", "用户原话明确表达当前行为",
                      "--evidence", "plan.md 与 src/one.py 的实际验证")
            self.assertEqual(self.read_state()["precheck"]["results"][q]["user_answer"], quote)
            if q == "Q1":
                self.call("accept", "--user-quote", "这一步可以了", succeeds=False)
        self.assertEqual(self.read_state()["phase"], "await_acceptance")
        self.call("accept", "--user-quote", "这一步符合我的预期，就按现在这样")
        self.assertEqual(self.read_state()["phase"], "await_next_step")
        self.assertEqual(self.read_state()["current_step"], 1)

    def test_single_confirmation_rejects_unoffered_choice_and_keeps_discussion(self):
        self.init_plan(steps=1)
        self.call("configure-git", "--mode", "off")
        self.call("authorize", "--step", "1", "--user-quote", "开始第一步")
        self.prepare_docs(1, choices=("A",), two_options=True)
        self.call("verified", "--result", "pass", "--evidence", "功能测试通过")
        self.call("documented")
        self.call("start-precheck")
        self.call("answer-precheck", "--id", "Q1", "--choice", "C",
                  "--user-answer", "第三种", "--summary", "选择未提供的选项",
                  "--evidence", "plan.md", succeeds=False)
        self.assertEqual(self.read_state()["precheck"]["attempts"], [])
        self.call("answer-precheck", "--id", "Q1", "--choice", "D",
                  "--user-answer", "我还没想清楚，能举个例子吗", "--summary", "期望仍未明确",
                  "--evidence", "plan.md")
        self.assertEqual(self.read_state()["phase"], "precheck_discussion")
        self.call("accept", "--user-quote", "通过", succeeds=False)
        self.call("resume-precheck", "--user-quote", "明白了，我希望保存后直接显示新记录")
        self.assertEqual(self.read_state()["phase"], "await_acceptance")

    def test_confirmation_requires_real_options_and_an_available_baseline(self):
        self.init_plan(steps=1)
        self.call("configure-git", "--mode", "off")
        self.call("authorize", "--step", "1", "--user-quote", "开始第一步")
        self.prepare_docs(1, choices=("A",), two_options=True)
        self.call("verified", "--result", "pass", "--evidence", "功能测试通过")
        self.call("documented")
        path = self.repo / "docs/ai-collab/demo/steps/01-step/preacceptance.md"
        original = path.read_text()
        for invalid in [original.replace("**当前约定选项**：A", "**当前约定选项**：C"),
                        original.replace("- B. 输入合法后仅显示提示\n", ""),
                        original.replace("### Q1", "### Note")]:
            with self.subTest(content=invalid):
                path.write_text(invalid)
                self.call("start-precheck", succeeds=False)
        path.write_text(original)
        self.call("start-precheck")

if __name__ == "__main__":
    unittest.main()
