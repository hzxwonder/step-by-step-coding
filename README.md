# Research Step-by-Step Coding

[简体中文](README.zh-CN.md) · English · [MIT license](LICENSE)

**Control research questions, experimental choices, and resources through clear examples and real results.**

The agent reads existing research materials, recommends a minimal experiment, implements, and checks the current step.
You control the research direction, comparisons, resources, and permission to continue. Read code explanations when needed.

You can inspect current research findings, formulas, data processing, prompts, configuration, logs, and outputs.
Short explanations support your current decision. Detailed evidence stays in the project documents.

The skill instructions, templates, and teaching documents use Simplified Chinese.
This README explains installation and use in English.

Computational MVPs are delivered as a narrated Jupyter notebook. Discuss the idea and adopt the steps first. A step can contain several cells. Chat handoffs aim for a five-second scan. Automatic short checks have a 60-second group limit. Long or unknown-duration cells require manual execution. [Open the runnable example](assets/mvp.ipynb). Routine implementation choices stay with the agent; questions focus on scientific meaning, resources, and permissions.

The agent restores research progress internally, preserving adopted scientific and resource decisions while adjusting engineering plans as needed. The notebook teaches the current method, control, and actual results through short code cells, reusing valid implementations. Concepts, examples, and diagrams are added when they help current understanding or you ask for them. The real comparison takes priority over tutorial completeness, layout, and explanations of every metric. Infrastructure uses established modules.

## What the skill does

- Discuss one core decision at a time, using examples to explain its effect on results, scope, or costs.
- Update the current experiment design when a decision changes. Reuse adopted methods, controls, data, metrics, decision rules, and budgets.
- Adopt a same-day step list. Save and hand off one Notebook step per turn for review and feedback.
- Explain the current question, observed facts, hypotheses, and why the next experiment is useful.
- Connect key agreements to checks and real evidence. Select tests or actual operations to match the change.
- Use consistent research terms, explain formula-to-code mappings, and provide detail when needed.
- Record confirmation sources and scope. Retain applicable decisions, and record authorization and acceptance separately.
- Show the current real case and separate execution validity, scientific findings, and user acceptance. Follow the user’s teaching and review cadence, and the agreed Git policy.

Valid negative results can complete a milestone. Successful execution does not establish scientific support. Learning questions help explain the observation; they are not acceptance requirements.
After a change, the agent tests the affected implementation and confirms only new, changed, or unresolved behavior.
The agent can use an earlier explicit request after it implements and verifies that request.

## How the conversation works

The agent explains one useful point at a time. It keeps detailed evidence in the project documents.
When you need to decide, it explains the current behavior and gives a recommendation. It offers alternatives only for real tradeoffs.
You can answer in your own words or ask for an example. You do not need to select a letter.

For example: **Should this experiment compare overall performance or test a specific mechanism?** This changes the controls and observations.
The agent connects your decision to formulas, code, and evaluation rules, then explains the result.
If you feel lost, it walks through the current case with a short explanation before adding detail. Existing valid checks are reused. The first comparison uses only its necessary path; feedback speed is improved after an informative observation.

The [Chinese notebook writing conventions](references/notebook-cells.md#中文教学写法与结果判读) specify terminology, metric denominators and comparison scales, distinguish percentage points from relative changes, and keep unrun, failed and inconclusive states separate. Figures identify units, comparators and statistical meaning; uncertainty names the actual missing evidence.

## Requirements

- A local Codex or Claude Code environment that supports skills.
- Git to install the skill and use the optional Git workflow.
- Python 3.9 or later to run the optional state helper and tests.
- Access to the project that you want to build.

The Python helpers use the standard library. They need no additional Python packages.
This repository supplies a standalone skill folder. It does not supply a plugin package or MCP server.

## Install

Choose one location for your coding agent. Run these commands in a macOS or Linux shell.
The destination directory must not already exist.

### Codex: use in all your local projects

```bash
mkdir -p "$HOME/.agents/skills"
git clone https://github.com/hzxwonder/step-by-step-coding.git "$HOME/.agents/skills/step-by-step-coding"
```

For one project, run these commands from that project's root instead:

```bash
mkdir -p .agents/skills
git clone https://github.com/hzxwonder/step-by-step-coding.git .agents/skills/step-by-step-coding
```

Codex detects skill changes automatically. If the skill does not appear, restart Codex.
In Codex CLI or the IDE extension, use `/skills` or type `$` to select the skill.
See the [official OpenAI documentation](https://learn.chatgpt.com/docs/build-skills).

If your Codex environment includes `$skill-installer`, you can ask it to install the repository root:

```text
$skill-installer Install hzxwonder/step-by-step-coding from GitHub.
Use repository path . and skill name step-by-step-coding.
```

The installer chooses its configured skill directory.
Use the manual commands above when you need a specific location.

### Claude Code: use in all your local projects

```bash
mkdir -p "$HOME/.claude/skills"
git clone https://github.com/hzxwonder/step-by-step-coding.git "$HOME/.claude/skills/step-by-step-coding"
```

For one project, use `.claude/skills/step-by-step-coding` as the clone destination.
Claude Code normally detects edits to skill files.
If you create a skills directory during a session, use `/reload-skills` if the skill does not appear.
See the [official Claude Code documentation](https://code.claude.com/docs/en/skills).

## Start a task

Open your target project in your coding agent.
Send this prompt in Codex:

```text
$step-by-step-coding 帮我根据当前实验包完成 MVP。我是科研初学者。
沿用核心 idea、已采用协议和有效结果，让 Notebook 从基本概念讲起，用实例、图解和短代码逐步实现核心方法，再讲清对照与观察。
```

In Claude Code, replace `$step-by-step-coding` with `/step-by-step-coding`.

The agent recovers the adopted design, budget, and valid results before planning further comparisons. The notebook uses ordinary language, explains each section’s purpose and what to look for, and introduces technical terms in everyday words. Experiment IDs, hashes, approvals, and management checklists stay in project records. Questions address unresolved choices that affect the hypothesis, fair comparisons, permissions, or cost.

The agent completes one adopted step per turn, using several cells when useful. It saves the Notebook and ends the turn for your review, execution or feedback. It integrates edits in place. A request to continue advances the next adopted step; individual cells do not need separate approval.

| Your message | What happens |
|---|---|
| `按当前方案开始` | Implement and hand off the current adopted step. Use bounded short checks or manual execution. |
| `继续` | Advance the next adopted step. Identify manual cells that still need results. |
| `解释一下这段代码` | Explain the current implementation or case. |
| `把这个对照换成……` | Review the effect on the question, fairness, and cost before changing the comparison. |
| `本轮符合预期` | Record acceptance of the displayed result within its actual scope. |

These are examples, not required phrases. The agent keeps the source and scope of your decisions. Resource permission and per-step handoffs are maintained separately. A request to continue does not establish scientific support or formal acceptance. New costs, permissions, or changes beyond the adopted scientific scope require the corresponding decision.

The agent runs only authorized, known short checks for the current step. The whole turn has a 60-second automatic-test limit. Long or unknown-duration cells require manual execution. Preparation addresses current-step blockers. It reuses SDKs, evaluation tools, raw responses, and concise logs. Unknown metadata blocks execution only when it affects the comparison or a real resource or permission limit. Missing cost evidence limits cost claims while preserving other valid observations. Small MVP findings retain their measured scope; formal experiments follow the adopted evaluation and statistical protocol.

## Files in your project

Notebook teaching uses a compact layout:

```text
mvp.ipynb              # Design, readable implementation, observations, and reproduction
.research/session.md   # Adopted sources, decisions, current milestone, and remaining work
evidence/              # Raw results and logs when needed
```

Existing protocols and results remain their source of truth. New explanations, examples, and code are integrated where they belong; affected parts are checked so the notebook remains readable and runnable from the start. Each update includes the existing real notebook URL and file link. Browser checks occur at the first teaching handoff or after relevant changes; layout and styling do not delay core computation.

Projects that explicitly use the state helper retain existing `docs/ai-collab/<task>/` records and `.ai-collab/` state. Templates are in `assets/`; see the [recording guide](references/alignment-mcq.md). State records reflect actual decisions and evidence; they do not create authorization, acceptance, or extra review steps. Explicit user pauses and acceptance points remain binding.

Keep personal answers and workflow state local. Before committing a project that uses the helper, add these patterns to that project’s `.gitignore`:

```gitignore
.ai-collab/
**/preacceptance-results*.md
```

The ignore file in this skill repository does not configure another project.

## Optional state helper

The agent can use `scripts/workflow.py` to record decisions and check recorded workflow transitions.
You can use the skill through conversation without typing the helper commands yourself.

From this repository's root, inspect the helper with:

```bash
python3 scripts/workflow.py --help
```

Always pass `--repo` before the command. Use it to identify the project that the helper should manage:

```bash
python3 scripts/workflow.py --repo /path/to/your-project status
```

`status` requires an initialized helper task. Conversation-based use does not require initialization.
The helper checks record structure; the agent checks authorization, scientific meaning, and real evidence. It does not run implementation tests or push commits.
Record sources, scope, case presentation, and evidence only when they exist. If a state transition cannot represent an authorized comparison, retain the state and record progress in the notebook; do not invent acceptance to unlock it.
After changes, review affected evidence and retain applicable confirmations. See the [behavior verification guide](references/behavior-verification.md).

`verified --result pass` records valid execution and evidence checks. The optional `--finding` records scientific interpretation separately.
Its values are `supports`, `does-not-support`, `inconclusive`, and the default `not-assessed`. Valid negative results can complete a step.
Implementation or evaluation errors still require correction.

For an explicit software task, the agent selects `init --focus software` without another task-type question.
See the [research workflow](references/research-workflow.md) for experimental design and evidence handling.

The optional [Claude Code hook example](references/guard-setup.md) restricts selected edit tools.
It does not cover shell commands or all other tools. It is not an operating system sandbox.
Keep the coding agent's permission controls active.

## Test the skill

Run these commands from this repository's root:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/workflow.py --help
```

The suite covers authorization boundaries, confirmations, design and source changes, partial revisions, and Git records.
It also tests the edit guard's path decisions.
The release tests include a macOS run. The GitHub workflow runs the suite on Ubuntu with Python 3.11.
Live Claude Code hook integration and Windows execution need separate validation.

## Update or uninstall

For the Codex user installation shown above, update with:

```bash
git -C "$HOME/.agents/skills/step-by-step-coding" pull --ff-only
```

Use your actual installation directory for other locations.
If Git reports local edits or divergent history, preserve your edits before you resolve the update.
The installer method may create a folder without Git history. Use its update instructions for that installation.

To uninstall, move the installed `step-by-step-coding` folder outside the agent's skill discovery directory.
Then refresh the agent's skill list. Keep the project plans and records that you still need.

## Repository contents

| Path | Purpose |
|---|---|
| [SKILL.md](SKILL.md) | Instructions that the coding agent reads. |
| [agents/openai.yaml](agents/openai.yaml) | Display name and example prompt for Codex. |
| [scripts/](scripts/) | State helper and optional edit guard. |
| [references/](references/) | Workflow rules and setup examples. |
| [assets/](assets/) | Plan, verification, explanation, and behavior templates. |
| [tests/](tests/) | Standard-library tests. |

See [the repository study](docs/repository-study.zh-CN.md) for the packaging sources and decisions.
The READMEs use short sentences, direct instructions, and consistent terms inspired by [ASD-STE100](https://www.asd-ste100.org/).
This writing approach does not claim formal STE certification.

## License

[MIT](LICENSE). Copyright 2026 hzxwonder.
