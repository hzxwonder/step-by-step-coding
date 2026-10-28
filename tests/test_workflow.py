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

    def confirm(self, *args, source_kind="requirement", source_ref="test:explicit-user-reply",
                scope="本项保存、显示或处理规则", succeeds=True):
        return self.call("answer-precheck", *args, "--source-kind", source_kind,
                         "--source-ref", source_ref, "--scope", scope, succeeds=succeeds)

    def present_case(self, succeeds=True):
        return self.call("present-case", "--case-id", "demo", "--kind", "real",
                         "--evidence", "runs/demo-case.json", "--presentation-ref", "test:shown-case-message",
                         "--summary", "输入 feature()，运行输出 ready，退出码为 0，与本步结果约定一致。",
                         succeeds=succeeds)

    def start_precheck(self):
        result = self.call("start-precheck")
        self.present_case()
        return result

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
        content = re.sub(r"(?m)^- \*\*首次可用步骤\*\*：.*$", "- **首次可用步骤**：01", "\n".join(lines) + "\n")
        master.write_text(content, encoding="utf-8")
        base = master.parent
        (base / "mvp-design.md").write_text(
            "# MVP 设计\n- **核心闭环**：用户从入口调用 feature()，看到 ready 结果并保存运行记录。\n"
            "主要功能：调用入口、展示结果。仅支持已约定的演示输入。\n", encoding="utf-8")
        (base / "technical-plan.md").write_text(
            "# 技术方案\n- **采用方案**：使用现有 Python 环境和标准库，以命令行输出并保存 JSON 记录。\n"
            "理由：本项目无需界面或外部服务，现有环境已经可用。\n", encoding="utf-8")
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
        self.call("approve-plan", "--user-quote", "认可刚展示的 MVP 设计、技术方案、路线和第一步计划")

    def prepare_docs(self, step, choices=("A", "B", "C", "A"), two_options=False):
        folder = self.repo / "docs" / "ai-collab" / "demo" / "steps" / f"{step:02d}-step"
        (folder / "verification.md").write_text("# 验证\n命令: python -m pytest; exit code 0; 通过。\n")
        (folder / "explain.md").write_text("# 代码讲解\n" + "解释真实输入、输出及边界条件和如何验证。" * 20)
        folder_source = self.repo / "src"
        folder_source.mkdir(exist_ok=True)
        (folder_source / ("one.py" if step == 1 else "two.py")).write_text("def feature():\n    return 'ready'\n")
        run = subprocess.run([sys.executable, "-c", f"from src.{'one' if step == 1 else 'two'} import feature; print(feature())"],
                             cwd=self.repo, text=True, capture_output=True, check=True)
        evidence = self.repo / "runs/demo-case.json"
        evidence.parent.mkdir(exist_ok=True)
        evidence.write_text(json.dumps({"input": "feature()", "stdout": run.stdout, "exit_code": run.returncode}))
        options = ("- A. 输入合法时展示新增结果\n"
                   "- B. 输入合法后仅显示提示\n"
                   + ("" if two_options else "- C. 输入合法后直接返回首页\n")
                   + "- D. 其他 / 不确定 / 想先讨论\n")
        (folder / "preacceptance.md").write_text("# 预验收\n" + "\n".join(
            f"### Q{i} 你希望这一步采用哪种行为？\n- **决策层级**：核心\n- **选择影响**：改变保存后的可见结果。\n" + options
            + f"- **当前约定选项**：{choice}\n"
            + "- **证据**：src/one.py 与当前步骤 plan.md\n"
            + "- **分歧处理**：讨论是否改变当前步骤范围\n"
            for i, choice in enumerate(choices, 1)
        ), encoding="utf8")

    def aligned_answer(self, i):
        choices = ["A", "B", "C", "A"]
        self.confirm( "--id", f"Q{i}", "--choice", choices[i-1],
                  "--user-answer", f"我选择{choices[i-1]}，这是我要的行为",
                  "--summary", "用户确认现行功能，与代码和步骤计划一致",
                  "--evidence", f"steps/0{self.read_state()['current_step']}-step/plan.md + src/one.py")

    def pass_precheck(self):
        self.start_precheck()
        for i in range(1, 5):
            self.aligned_answer(i)

    def prepare_direct_precheck(self, count=1):
        self.init_plan(steps=2)
        for path in ("prompts/task.txt", "config/run.json", "outputs/demo/run.log"):
            self.call("allow-path", "--step", "1", "--path", path)
        self.call("configure-git", "--mode", "off")
        self.call("authorize", "--step", "1", "--user-quote", "按计划开始第一步")
        self.prepare_docs(1)
        for path, content in (("prompts/task.txt", "返回记录中的金额，不补写缺失值。"),
                              ("config/run.json", '{"missing_amount": null}'),
                              ("outputs/demo/run.log", "start case=demo\ndone records=2\n")):
            file = self.repo / path
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(content)
        folder = self.repo / "docs/ai-collab/demo/steps/01-step"
        (folder / "explain.md").write_text("# 结果\n运行 demo 生成两条记录。日志位于 outputs/demo/run.log，命令行可再次运行 demo。\n")
        agreements = ["界面显示汇总结果", "prompt 不补写缺失金额", "配置保留缺失金额为空",
                      "保留完整运行日志", "结果包含两条记录", "金额使用元作为单位", "旧结果保留在独立目录"]
        (folder / "preacceptance.md").write_text("\n".join(
            f"### Q{i} {behavior}\n- **决策层级**：核心\n- **选择影响**：改变该结果的生成或核对方式。\n- **当前约定**：{behavior}。\n"
            "- **证据**：步骤计划、实际 prompt、生效配置和本次运行日志。\n"
            "- **分歧处理**：核对受影响实现并重跑 demo。\n"
            for i, behavior in enumerate(agreements[:count], 1)))
        self.call("verified", "--result", "pass", "--evidence", "demo 真实运行记录与结果已核对")

    def test_direct_agreements_reuse_one_explicit_acceptance_and_authorization(self):
        self.prepare_direct_precheck(count=7)
        self.call("documented")
        self.start_precheck()
        quote = "展示的约定和结果都符合预期，验收第一步并开始第二步"
        for i in range(1, 8):
            self.confirm( "--id", f"Q{i}", "--user-answer", quote,
                      "--summary", "用户接受整份结果，此原话明确覆盖本项约定",
                      "--evidence", "当前步骤计划与 demo 运行记录")
        self.call("accept", "--user-quote", quote)
        self.assertEqual(self.read_state()["phase"], "await_next_step")
        self.assertEqual(self.read_state()["current_step"], 1)
        self.call("authorize", "--step", "2", "--user-quote", quote)
        self.assertEqual(self.read_state()["current_step"], 2)

    def test_short_explanation_is_valid_but_empty_document_is_not(self):
        self.prepare_direct_precheck()
        path = self.repo / "docs/ai-collab/demo/steps/01-step/explain.md"
        concise = path.read_text()
        self.assertLess(len(concise), 300)
        path.write_text(" \n")
        self.call("documented", succeeds=False)
        path.write_text(concise)
        self.call("documented")
        self.assertEqual(self.read_state()["phase"], "precheck_setup")

    def test_explanation_updates_preserve_locked_evidence_and_confirmation(self):
        self.prepare_direct_precheck()
        self.call("documented")
        self.start_precheck()
        state_path = self.repo / ".ai-collab/demo/state.json"
        state = self.read_state()
        explanation = "docs/ai-collab/demo/steps/01-step/explain.md"
        state["precheck"]["source_hashes"][explanation] = "previous-explanation-fingerprint"
        state_path.write_text(json.dumps(state))
        (self.repo / explanation).write_text("# 使用方式\n运行 demo。查看汇总表。金额单位是元。\n")
        self.confirm( "--id", "Q1", "--user-answer", "界面就按这个结果显示",
                  "--summary", "原话明确确认显示方式", "--evidence", "demo 结果")
        self.call("accept", "--user-quote", "结果符合预期")
        self.assertEqual(self.read_state()["accepted_steps"], [1])

    def test_actual_prompt_config_and_log_changes_block_acceptance(self):
        self.prepare_direct_precheck()
        self.call("documented")
        self.start_precheck()
        self.confirm( "--id", "Q1", "--user-answer", "显示方式符合预期",
                  "--summary", "已核对", "--evidence", "demo 结果")
        for path in ("prompts/task.txt", "config/run.json", "outputs/demo/run.log"):
            with self.subTest(path=path):
                file = self.repo / path
                original = file.read_bytes()
                file.write_text("changed after verification")
                self.call("accept", "--user-quote", "验收", succeeds=False)
                file.write_bytes(original)
        self.call("accept", "--user-quote", "已核对的结果符合预期")

    def test_direct_discussion_resumes_the_correct_item_out_of_order(self):
        self.prepare_direct_precheck(count=2)
        self.call("documented")
        self.start_precheck()
        self.confirm( "--id", "Q2", "--user-answer", "我还想了解缺失金额的处理",
                  "--summary", "仍需讨论", "--evidence", "实际 prompt", "--needs-discussion")
        self.assertEqual(self.read_state()["phase"], "precheck_discussion")
        self.call("accept", "--user-quote", "接受", succeeds=False)
        self.call("resume-precheck", "--source-ref", "test:clarifying-user-message", "--user-quote", "明白了，缺失金额就保留为空")
        self.assertEqual(list(self.read_state()["precheck"]["results"]), ["Q2"])
        self.assertEqual(self.read_state()["phase"], "precheck")

    def test_direct_agreement_still_requires_real_quote_and_separate_step_acceptance(self):
        self.prepare_direct_precheck()
        self.call("documented")
        self.start_precheck()
        self.confirm( "--id", "Q1", "--user-answer", "",
                  "--summary", "已核对", "--evidence", "demo 结果", succeeds=False)
        self.assertEqual(self.read_state()["precheck"]["attempts"], [])
        self.confirm( "--id", "Q1", "--user-answer", "界面就这样显示",
                  "--summary", "只确认显示方式", "--evidence", "demo 结果")
        self.assertEqual(self.read_state()["phase"], "await_acceptance")
        self.call("authorize", "--step", "2", "--user-quote", "开始第二步", succeeds=False)

    def test_direct_agreement_rejects_ambiguous_or_empty_records(self):
        self.prepare_direct_precheck()
        self.call("documented")
        path = self.repo / "docs/ai-collab/demo/steps/01-step/preacceptance.md"
        original = path.read_text()
        invalid_records = [
            original.replace("**当前约定**：界面显示汇总结果。", "**当前约定**： "),
            original.replace("**证据**：步骤计划、实际 prompt、生效配置和本次运行日志。", "**证据**： "),
            original + "\n- A. 另一个未确认的行为\n",
            original + "\n- **当前约定选项**：A\n",
        ]
        for invalid in invalid_records:
            with self.subTest(record=invalid):
                path.write_text(invalid)
                self.call("start-precheck", succeeds=False)
        path.write_text(original)
        self.start_precheck()

    def test_optional_choice_does_not_assume_agreement_for_choice_items(self):
        self.init_plan(steps=1)
        self.call("configure-git", "--mode", "off")
        self.call("authorize", "--step", "1", "--user-quote", "开始第一步")
        self.prepare_docs(1, choices=("A",), two_options=True)
        self.call("verified", "--result", "pass", "--evidence", "demo 结果已核对")
        self.call("documented")
        self.start_precheck()
        self.confirm( "--id", "Q1", "--user-answer", "我不确定",
                  "--summary", "尚未决定", "--evidence", "demo 结果", succeeds=False)
        self.assertEqual(self.read_state()["precheck"]["attempts"], [])

    def test_statement_after_evidence_cannot_keep_confirmation_after_behavior_change(self):
        self.prepare_direct_precheck()
        self.call("documented")
        path = self.repo / "docs/ai-collab/demo/steps/01-step/preacceptance.md"
        text = path.read_text().replace("- **当前约定**：界面显示汇总结果。\n", "")
        path.write_text(text + "\n- **当前约定**：界面显示汇总结果。\n")
        self.start_precheck()
        self.confirm( "--id", "Q1", "--user-answer", "显示汇总结果就行",
                  "--summary", "确认显示方式", "--evidence", "demo 结果")
        self.call("reset-precheck", "--user-quote", "改成仅显示完成提示")
        path.write_text(path.read_text().replace("界面显示汇总结果。", "界面仅显示完成提示。"))
        self.start_precheck()
        self.assertEqual(self.read_state()["precheck"]["results"], {})
        self.assertEqual(self.read_state()["phase"], "precheck")

    def test_guard_allows_next_step_planning_without_code_authorization(self):
        self.init_plan(steps=2)
        self.call("configure-git", "--mode", "off")
        def check(path):
            return guard.check({"tool_name": "Write", "tool_input": {"file_path": str(self.repo / path)}}, self.repo)
        self.assertIsNone(check("docs/ai-collab/demo/steps/01-step/plan.md"))
        self.assertIsNotNone(check("src/one.py"))
        self.call("authorize", "--step", "1", "--user-quote", "开始第一步")
        self.prepare_docs(1)
        self.call("verified", "--result", "pass", "--evidence", "demo 已验证")
        self.call("documented")
        self.pass_precheck()
        self.call("accept", "--user-quote", "第一步符合预期")
        self.assertIsNone(check("docs/ai-collab/demo/steps/02-step/plan.md"))
        self.assertIsNotNone(check("docs/ai-collab/demo/steps/01-step/plan.md"))
        self.assertIsNotNone(check("src/two.py"))

    def test_core_pending_decision_precedes_presentation_preference(self):
        self.prepare_direct_precheck(count=2)
        self.call("documented")
        path = self.repo / "docs/ai-collab/demo/steps/01-step/preacceptance.md"
        path.write_text(path.read_text().replace("**决策层级**：核心", "**决策层级**：体验", 1))
        result = self.call("start-precheck")
        self.assertEqual(self.read_state()["precheck"]["levels"], {"Q1": "体验", "Q2": "核心"})
        self.assertIn("Q2", result.stdout)
        self.confirm("--id", "Q2", "--user-answer", "缺失金额不要补写",
                     "--summary", "核心处理规则已确认", "--evidence", "实际 prompt")
        self.assertEqual(set(self.read_state()["precheck"]["results"]), {"Q2"})

    def test_decision_requires_its_actual_impact(self):
        self.prepare_direct_precheck()
        self.call("documented")
        path = self.repo / "docs/ai-collab/demo/steps/01-step/preacceptance.md"
        path.write_text(path.read_text().replace("- **选择影响**：改变该结果的生成或核对方式。\n", ""))
        self.call("start-precheck", succeeds=False)

    def test_launch_authorization_and_agent_choice_are_not_requirement_confirmation(self):
        self.prepare_direct_precheck()
        self.call("documented")
        self.start_precheck()
        self.call("answer-precheck", "--id", "Q1", "--user-answer", "开始第 1 步",
                  "--summary", "已核对实现", "--evidence", "verification.md", succeeds=False)
        for source_kind in ("authorization", "agent-choice"):
            with self.subTest(source_kind=source_kind):
                self.confirm("--id", "Q1", "--user-answer", "开始第 1 步",
                             "--summary", "实施授权", "--evidence", "verification.md",
                             source_kind=source_kind, succeeds=False)
        self.assertEqual(self.read_state()["precheck"]["results"], {})
        self.assertEqual(self.read_state()["precheck"]["attempts"], [])

    def test_requirement_delegation_and_plan_keep_their_source_and_scope(self):
        self.prepare_direct_precheck(count=3)
        self.call("documented")
        self.start_precheck()
        sources = [("Q1", "requirement", "message:display", "界面显示汇总结果", "显示汇总结果"),
                   ("Q2", "delegation", "message:prompt", "prompt 措辞你来定，金额缺失不要补写", "金额规则内的 prompt 措辞"),
                   ("Q3", "approved-plan", "message:approval; plan.md#amount", "采用刚展示的缺失金额方案", "该版本计划的缺失金额规则")]
        for qid, kind, reference, quote, scope in sources:
            self.confirm("--id", qid, "--user-answer", quote, "--summary", "原话覆盖当前行为",
                         "--evidence", "当前版本运行记录", source_kind=kind, source_ref=reference, scope=scope)
            record = self.read_state()["precheck"]["results"][qid]
            self.assertEqual((record["source_kind"], record["source_ref"], record["scope"]), (kind, reference, scope))
        self.call("accept", "--user-quote", "本次展示结果符合预期")

    def test_confirmation_without_source_or_scope_stays_pending(self):
        self.prepare_direct_precheck()
        self.call("documented")
        self.start_precheck()
        for field in ("source_ref", "scope"):
            with self.subTest(field=field):
                self.confirm("--id", "Q1", "--user-answer", "按这个方式显示",
                             "--summary", "显示方式确认", "--evidence", "运行记录",
                             **{field: ""}, succeeds=False)
        self.assertEqual(self.read_state()["precheck"]["results"], {})

    def test_user_question_is_recorded_as_discussion_not_confirmation(self):
        self.prepare_direct_precheck()
        self.call("documented")
        self.start_precheck()
        self.confirm("--id", "Q1", "--user-answer", "能先给我看一个实际例子吗？",
                     "--summary", "用户仍需了解结果", "--evidence", "demo 结果",
                     source_kind="discussion", source_ref="message:question", scope="汇总结果的展示方式")
        self.assertEqual(self.read_state()["phase"], "precheck_discussion")
        self.assertEqual(self.read_state()["precheck"]["results"], {})
        self.call("resume-precheck", "--user-quote", "看过例子了，汇总结果就这样显示",
                  "--source-ref", "message:explicit-confirmation")
        record = self.read_state()["precheck"]["results"]["Q1"]
        self.assertEqual(record["source_kind"], "requirement")
        self.assertEqual(record["source_ref"], "message:explicit-confirmation")

    def test_passing_checks_and_confirmations_do_not_replace_real_case_presentation(self):
        self.prepare_direct_precheck()
        self.call("documented")
        self.call("start-precheck")
        self.confirm("--id", "Q1", "--user-answer", "界面这样显示",
                     "--summary", "已有明确要求", "--evidence", "运行记录")
        self.call("accept", "--user-quote", "验收", succeeds=False)
        for kind, evidence, presentation in [("simulated", "runs/demo-case.json", "message:shown"),
                                              ("not-run", "runs/demo-case.json", "message:shown"),
                                              ("real", "runs/missing.json", "message:shown"),
                                              ("real", "runs/demo-case.json", "")]:
            with self.subTest(kind=kind, evidence=evidence, presentation=presentation):
                self.call("present-case", "--case-id", "demo", "--kind", kind, "--evidence", evidence,
                          "--presentation-ref", presentation, "--summary", "展示本次输入、日志与结果", succeeds=False)
        self.present_case()
        self.call("accept", "--user-quote", "这次展示的结果符合预期")

    def test_case_evidence_changes_and_revision_require_current_case_presentation(self):
        self.prepare_direct_precheck()
        self.call("documented")
        self.start_precheck()
        self.confirm("--id", "Q1", "--user-answer", "显示汇总结果",
                     "--summary", "显示方式已明确", "--evidence", "demo 结果")
        evidence = self.repo / "runs/demo-case.json"
        evidence.write_text(evidence.read_text() + "\n")
        self.call("accept", "--user-quote", "验收", succeeds=False)
        self.call("revise", "--user-quote", "按原计划修复当前步骤")
        self.assertNotIn("case_presentation", self.read_state()["precheck"])
        self.call("verified", "--result", "pass", "--evidence", "已重新核对")
        self.call("documented")
        self.call("start-precheck")
        self.assertEqual(set(self.read_state()["precheck"]["results"]), {"Q1"})
        self.call("accept", "--user-quote", "验收", succeeds=False)
        self.present_case()
        self.call("accept", "--user-quote", "当前结果已验收")

    def test_existing_valid_source_and_shown_case_survive_record_only_reset(self):
        self.prepare_direct_precheck()
        self.call("documented")
        self.start_precheck()
        self.confirm("--id", "Q1", "--user-answer", "界面显示汇总结果",
                     "--summary", "明确需求", "--evidence", "demo 结果")
        previous = self.read_state()["precheck"]
        self.call("reset-precheck", "--user-quote", "按已确认要求整理记录")
        self.call("start-precheck")
        current = self.read_state()["precheck"]
        self.assertEqual(current["results"], previous["results"])
        self.assertEqual(current["case_presentation"], previous["case_presentation"])
        self.call("accept", "--user-quote", "此前展示的同版本结果符合预期")

    def test_old_record_without_provenance_cannot_be_reused_as_confirmed(self):
        self.prepare_direct_precheck()
        self.call("documented")
        self.start_precheck()
        self.confirm("--id", "Q1", "--user-answer", "显示汇总结果",
                     "--summary", "已确认", "--evidence", "demo 结果")
        state = self.read_state()
        for field in ("source_kind", "source_ref", "scope"):
            state["precheck"]["results"]["Q1"].pop(field)
        (self.repo / ".ai-collab/demo/state.json").write_text(json.dumps(state))
        self.call("accept", "--user-quote", "验收", succeeds=False)
        self.call("reset-precheck", "--user-quote", "沿用此前显示汇总结果的要求")
        self.call("start-precheck")
        self.assertEqual(self.read_state()["precheck"]["results"], {})
        self.confirm("--id", "Q1", "--user-answer", "显示汇总结果",
                     "--summary", "补齐已有原话的来源和范围，无需再次提问", "--evidence", "demo 结果")
        self.call("accept", "--user-quote", "当前结果符合预期")

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

    def test_design_and_technical_proposal_required_before_approval(self):
        self.call("init", "--slug", "demo", "--title", "示范", "--steps", "1")
        self.fill_plan_rationale(1)
        base = self.repo / "docs/ai-collab/demo"
        for name in ("mvp-design.md", "technical-plan.md"):
            path = base / name
            valid_text = path.read_text()
            for invalid_text in ("", (SKILL / "assets" / name).read_text()):
                path.write_text(invalid_text)
                self.call("approve-plan", "--user-quote", "认可已展示的设计和方案", succeeds=False)
                self.assertEqual(self.read_state()["phase"], "planning")
            path.unlink()
            self.call("approve-plan", "--user-quote", "认可", succeeds=False)
            path.write_text(valid_text)
        self.call("approve-plan", "--user-quote", "认可已展示的设计和方案")
        self.assertEqual(self.read_state()["accepted_steps"], [])

    def test_first_usable_step_must_be_in_route(self):
        self.call("init", "--slug", "demo", "--title", "示范", "--steps", "2")
        self.fill_plan_rationale(2)
        master = self.repo / "docs/ai-collab/demo/plan.md"
        valid_text = master.read_text()
        for milestone in ("", "00", "03", "以后决定"):
            master.write_text(valid_text.replace("**首次可用步骤**：01", "**首次可用步骤**：" + milestone))
            self.call("approve-plan", "--user-quote", "认可", succeeds=False)
        master.write_text(valid_text)
        self.call("approve-plan", "--user-quote", "认可第一步跑通的设计与计划")

    def test_later_mvp_requires_concrete_preparation(self):
        self.call("init", "--slug", "demo", "--title", "示范", "--steps", "2")
        self.fill_plan_rationale(2)
        master = self.repo / "docs/ai-collab/demo/plan.md"
        text = master.read_text().replace("**首次可用步骤**：01", "**首次可用步骤**：02")
        master.write_text(text)
        self.call("approve-plan", "--user-quote", "认可", succeeds=False)
        master.write_text(re.sub(r"(?m)^- \*\*必要准备\*\*：.*$",
                                "- **必要准备**：需先在设备上安装已确认的运行时，随后在第二步完成真实设备输入与结果展示。", text))
        self.call("approve-plan", "--user-quote", "认可先准备设备再跑通的设计与计划")

    def test_future_details_can_wait_until_their_authorization(self):
        self.call("init", "--slug", "demo", "--title", "示范", "--steps", "2")
        self.fill_plan_rationale(2)
        self.call("allow-path", "--step", "1", "--path", "src/one.py")
        self.call("allow-path", "--step", "2", "--path", "src/two.py")
        future = self.repo / "docs/ai-collab/demo/steps/02-step/plan.md"
        future.write_text((SKILL / "assets/step-plan.md").read_text())
        self.call("approve-plan", "--user-quote", "认可 MVP 和后续概要，第二步实施前细化")
        self.call("configure-git", "--mode", "off")
        self.call("authorize", "--step", "1", "--user-quote", "开始 MVP")
        self.prepare_docs(1)
        self.call("verified", "--result", "pass", "--evidence", "真实示例已运行")
        self.call("documented")
        self.pass_precheck()
        self.call("accept", "--user-quote", "这个版本符合预期")
        self.call("authorize", "--step", "2", "--user-quote", "开始第二步", succeeds=False)
        self.fill_plan_rationale(2)
        self.call("authorize", "--step", "2", "--user-quote", "认可细化内容并开始第二步")

    def test_design_guard_allows_scoped_prototype_before_implementation(self):
        self.call("init", "--slug", "demo", "--title", "示范", "--steps", "1")
        def check(path):
            return guard.check({"tool_name": "Write", "tool_input": {"file_path": str(self.repo / path)}}, self.repo)
        for name in ("mvp-design.md", "technical-plan.md", "prototype.html"):
            self.assertIsNone(check("docs/ai-collab/demo/" + name))
            self.assertIsNotNone(check("docs/ai-collab/other/" + name))
        self.assertIsNotNone(check("src/app.html"))
        self.assertIsNotNone(check("package.json"))
        self.assertIsNotNone(check("docs/ai-collab/demo/backend.py"))
        self.fill_plan_rationale(1)
        self.call("approve-plan", "--user-quote", "认可设计和计划")
        self.call("configure-git", "--mode", "off")
        self.assertIsNone(check("docs/ai-collab/demo/prototype.html"))
        self.assertIsNotNone(check("src/app.html"))

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
        self.start_precheck()
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
        self.confirm( "--id", "Q1", "--choice", "A", "--user-answer", "A", "--summary", "同意", "--evidence", "plan.md", succeeds=False)
        self.start_precheck()
        self.confirm( "--id", "Q5", "--choice", "B", "--user-answer", "B", "--summary", "同意", "--evidence", "plan.md", succeeds=False)
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
        self.start_precheck()
        self.confirm( "--id", "Q1", "--choice", "B",
                  "--user-answer", "我希望只弹出提示", "--summary", "用户期望与当前已实现行为不同",
                  "--evidence", "plan.md + src/one.py")
        self.assertEqual(self.read_state()["phase"], "precheck_discussion")
        self.assertEqual(self.read_state()["precheck"]["results"], {})
        self.confirm( "--id", "Q2", "--choice", "B", "--user-answer", "B", "--summary", "同意", "--evidence", "plan.md", succeeds=False)
        self.call("accept", "--user-quote", "已经验收", succeeds=False)
        self.call("resume-precheck", "--source-ref", "test:clarifying-user-message", "--user-quote", "听了说明，我决定保留目前方案")
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
        self.start_precheck()
        self.confirm( "--id", "Q1", "--choice", "D", "--user-answer", "不确定，我想先看看实际界面", "--summary", "需要实例",
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
        self.start_precheck()
        self.confirm( "--id", "Q1", "--choice", "A", "--needs-discussion",
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
        self.start_precheck()
        self.aligned_answer(1)
        file = self.repo / "docs/ai-collab/demo/steps/01-step/preacceptance.md"
        file.write_text(file.read_text() + "\n新增不一样的说明\n")
        self.confirm( "--id", "Q2", "--choice", "B", "--user-answer", "我选择B", "--summary", "同意", "--evidence", "src/one.py", succeeds=False)
        self.call("reset-precheck", "--user-quote", "题目有歧义，同意重新开始")
        self.start_precheck()
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
        self.start_precheck()
        self.aligned_answer(1)
        source = self.repo / "src" / "one.py"
        source.write_text(source.read_text() + "\n# stealth change\n")
        self.confirm( "--id", "Q2", "--choice", "B", "--user-answer", "B", "--summary", "同意", "--evidence", "plan.md", succeeds=False)
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
        self.start_precheck()
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
        self.start_precheck()
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
        self.start_precheck()
        self.assertEqual(self.read_state()["phase"], "await_acceptance")
        self.call("accept", "--user-quote", "正式验收")

    def test_existing_confirmation_state_resumes_without_new_options_field(self):
        self.init_plan(steps=1)
        self.call("configure-git", "--mode", "off")
        self.call("authorize", "--step", "1", "--user-quote", "开始第一步")
        self.prepare_docs(1)
        self.call("verified", "--result", "pass", "--evidence", "功能测试通过")
        self.call("documented")
        self.start_precheck()
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
        self.start_precheck()
        for q, choice, quote in [("Q1", "A", "保存后就让我看到新记录"),
                                  ("Q2", "B", "这里只提醒我保存好了就行")]:
            self.confirm( "--id", q, "--choice", choice,
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
        self.start_precheck()
        self.confirm( "--id", "Q1", "--choice", "C",
                  "--user-answer", "第三种", "--summary", "选择未提供的选项",
                  "--evidence", "plan.md", succeeds=False)
        self.assertEqual(self.read_state()["precheck"]["attempts"], [])
        self.confirm( "--id", "Q1", "--choice", "D",
                  "--user-answer", "我还没想清楚，能举个例子吗", "--summary", "期望仍未明确",
                  "--evidence", "plan.md")
        self.assertEqual(self.read_state()["phase"], "precheck_discussion")
        self.call("accept", "--user-quote", "通过", succeeds=False)
        self.call("resume-precheck", "--source-ref", "test:clarifying-user-message", "--user-quote", "明白了，我希望保存后直接显示新记录")
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
        self.start_precheck()

if __name__ == "__main__":
    unittest.main()
