# Research Step-by-Step Coding

[简体中文](README.zh-CN.md) · English · [MIT license](LICENSE)

**Control research questions, experimental choices, and resources through clear examples and real results.**

The agent reads existing research materials, recommends a minimal experiment, implements, and checks the current step.
You control the research direction, comparisons, resources, and permission to continue. Read code explanations when needed.

You can inspect current research findings, formulas, data processing, prompts, configuration, logs, and outputs.
Short explanations support your current decision. Detailed evidence stays in the project documents.

The skill instructions, templates, and teaching documents use Simplified Chinese.
This README explains installation and use in English.

Computational MVPs are delivered as a narrated Jupyter notebook. [Open the runnable example](assets/mvp.ipynb). Routine implementation choices stay with the agent; questions focus on scientific meaning, resources, and permissions.

## What the skill does

- Discuss one core decision at a time, using examples to explain its effect on results, scope, or costs.
- Return the minimal experiment design after each design discussion. Define methods, controls, data, metrics, decision rules, resources, and implementation.
- Run the core comparison early after design approval and permission to begin. Extend experiments as the evidence requires.
- Explain the current question, observed facts, hypotheses, and why the next experiment is useful.
- Connect key agreements to checks and real evidence. Select tests or actual operations to match the change.
- Use consistent research terms, explain formula-to-code mappings, and provide detail when needed.
- Record confirmation sources and scope. Retain applicable decisions, and record authorization and acceptance separately.
- Show a real case before acceptance. Separate execution validity, scientific findings, and user acceptance. Save under the agreed Git policy.

Acceptance checks implementation and experiment agreements. Valid negative results can complete a step. Successful execution does not establish scientific support.
After a change, the agent tests the affected implementation and confirms only new, changed, or unresolved behavior.
The agent can use an earlier explicit request after it implements and verifies that request.

## How the conversation works

The agent explains one useful point at a time. It keeps detailed evidence in the project documents.
When you need to decide, it explains the current behavior and gives a recommendation. It offers alternatives only for real tradeoffs.
You can answer in your own words or ask for an example. You do not need to select a letter.

For example: **Should this experiment compare overall performance or test a specific mechanism?** This changes the controls and observations.
The agent connects your decision to formulas, code, and evaluation rules, then explains the result.
If you feel lost, it explains a smaller example before it introduces more terms.

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
$step-by-step-coding 帮我验证这个研究模块是否有效。我是科研初学者。
先接续已有协议，讨论最小实验、对照、指标和预算，再按认可与授权逐步实现。
```

In Claude Code, replace `$step-by-step-coding` with `/step-by-step-coding`.

After each design discussion, the agent returns the current minimal experiment design and references existing protocols.
Experiment tables, samples, and output examples support decisions. HTML prototypes are used when an interactive tool is required.
One explicit reply can approve the designs and route, and authorize the first step. Later steps need only outlines until implementation approaches.
Files stay local by default. If you request remote backups, the agent confirms only the missing destination and branch details.
If you choose a push, confirm the repository and branch.

Use these messages as the task proceeds:

| Your message | What it authorizes |
|---|---|
| `确认需求，生成计划` | Create the main plan and the step plans. |
| `认可刚展示的实验设计、技术方案和计划` | Approve the displayed designs and plans. Implementation still needs permission to start. |
| `开始第 1 步` | Implement the first step under the approved plan. |
| `解释一下这段代码` | Explain the current implementation. |
| `开始预验收` | Check key agreements. Ask only about unresolved decisions. |
| `本步骤验收通过` | Accept the current step after behavior confirmation. |
| `开始第 2 步` | Start the next step. |

The messages above are examples. You can use other words that clearly express the same decision.
For example, “这一步符合我的预期，就这样” accepts the current step after behavior confirmation.
The agent interprets your reply in context and records your actual words.

Plan approval, step acceptance, and permission to start the next step are separate decisions.
One explicit statement can cover several decisions. The agent records each decision without asking again. One decision does not imply the others.

## Files in your project

The agent creates these files in the project that you develop:

```text
docs/ai-collab/<task>/
├── plan.md
├── mvp-design.md
├── technical-plan.md
├── prototype.html  # When an interactive tool is required
└── steps/01-step/
    ├── plan.md
    ├── verification.md
    ├── explain.md
    ├── preacceptance.md
    └── preacceptance-results.md

.ai-collab/<task>/state.json
.ai-collab/active.json
```

`mvp-design.md` defines the minimal experiment, decision rules, and resource limits. `technical-plan.md` records implementation sources, data flow, and evaluation.
`plan.md` defines the first usable milestone and later steps. `verification.md` records actual test results.
`explain.md` explains the result and implementation. `preacceptance.md` records key agreements and evidence.
The results file records your answers. The `.ai-collab` files record workflow state.

Keep personal answers and workflow state local.
Add these patterns to your target project's `.gitignore` before a commit:

```gitignore
.ai-collab/
**/preacceptance-results*.md
```

The ignore file in this skill repository does not configure another project's ignore rules.

## Optional state helper

The agent can use `scripts/workflow.py` to record approvals and enforce valid workflow transitions.
You can use the skill through conversation without typing the helper commands yourself.

From this repository's root, inspect the helper with:

```bash
python3 scripts/workflow.py --help
```

Always pass `--repo` before the command. Use it to identify the project that the helper should manage:

```bash
python3 scripts/workflow.py --repo /path/to/your-project status
```

`status` requires an initialized task. Ask the agent to initialize the workflow when you approve the planning work.
The helper does not execute implementation tests, judge your answers, or push commits.
The agent must run each test and record the actual evidence.

Confirmation records require a source type, message reference, and scope. Authorization and agent choices cannot count as requirement confirmation.
Acceptance also requires a recorded real-case presentation and an evidence file. The agent must check the meaning of the reply and the actual execution evidence.

New tasks default to `research`. Plan approval checks the research question, decision rules, resource limits, core flow, and implementation proposal.
Later steps need detail before authorization. Existing tasks retain their earlier plan requirements.
The helper checks structure. The agent must check comparison validity, evidence quality, and authorization against actual materials and conversation.

Acceptance checks include the experiment design, implementation plan, and optional HTML prototype. They detect edits, creation, and deletion.
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
