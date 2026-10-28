# Step-by-Step Coding

[简体中文](README.zh-CN.md) · English · [MIT license](LICENSE)

**Describe the result you want. Use examples and real runs to control the scope and pace of development.**

The agent investigates, recommends, implements, and verifies.
You decide key behavior, accept each result, and authorize the next step. Read code explanations when you need them.

For each step, the agent presents the result, evidence, and key implementation details. Read code explanations when you need them.
You decide whether to revise the work, accept the step, or continue.

This skill helps an AI coding agent discuss requirements, write plans, implement one step, test the result, and explain the code.
You decide when each step starts and when it is complete.

The skill instructions, templates, and teaching documents use Simplified Chinese.
This README explains installation and use in English.

## What the skill does

- Ask one question at a time, with a concrete example when useful.
- Discuss MVP features and scope first. Return the updated short design after each design discussion.
- Provide an editable HTML prototype for product design. Research and discuss the stack, then write the technical plan.
- Start implementation after design approval and permission to begin. Deliver the core flow early, then improve it incrementally.
- Emphasize key decisions in bold. Explain necessary terms before you use them.
- Explain why each planned step is necessary.
- Get approval for the overall route and the current step details.
- Implement only the step that you authorize.
- Test the result and explain the actual code.
- Compare the implemented behavior with your expectations.
- Resolve core decisions about the solution, success criteria, scope, and major costs before presentation preferences.
- Record each confirmation's source and scope. Record permission to start separately.
- Show a real case with key implementation details, logs, output, and reasoning before acceptance.
- Retain confirmed behavior when it does not change.
- Commit and push accepted work only under your chosen Git policy.

The behavior questions confirm the required behavior. They do not test your knowledge of code or terminology.
After a change, the agent tests the affected implementation and confirms only new, changed, or unresolved behavior.
The agent can use an earlier explicit request after it implements and verifies that request.

## How the conversation works

The agent explains one useful point at a time. It keeps detailed evidence in the project documents.
When you need to decide, it explains the current behavior and gives a recommendation. It offers alternatives only for real tradeoffs.
You can answer in your own words or ask for an example. You do not need to select a letter.

For example: **Should each save replace the previous record, or keep the previous record too?**
The agent connects your decision to the relevant code and explains the result.
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
$step-by-step-coding 帮我做一个本地记账工具。我是初学者。
先用具体例子对齐结果，给出建议，再按批准的步骤实施。
```

In Claude Code, replace `$step-by-step-coding` with `/step-by-step-coding`.

After each design discussion, the agent returns the current MVP design. The technical plan and product prototype help you decide.
One explicit reply can approve the designs and route, and authorize the first step. Later steps need only outlines until implementation approaches.
Files stay local by default. If you request remote backups, the agent confirms only the missing destination and branch details.
If you choose a push, confirm the repository and branch.

Use these messages as the task proceeds:

| Your message | What it authorizes |
|---|---|
| `确认需求，生成计划` | Create the main plan and the step plans. |
| `认可刚展示的 MVP 设计、技术方案和计划` | Approve the displayed designs and plans. Implementation still needs permission to start. |
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
├── prototype.html  # For product design
└── steps/01-step/
    ├── plan.md
    ├── verification.md
    ├── explain.md
    ├── preacceptance.md
    └── preacceptance-results.md

.ai-collab/<task>/state.json
.ai-collab/active.json
```

`mvp-design.md` defines the main features and scope choices. `technical-plan.md` records the stack, reasons, and runtime approach.
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

Plan approval checks the core MVP flow, technical proposal, and first usable milestone. Later steps need detail before their own authorization.
The helper checks basic structure. The agent must check feature choices, design approval, and the product prototype against the actual conversation.

The optional [Claude Code hook example](references/guard-setup.md) restricts selected edit tools.
It does not cover shell commands or all other tools. It is not an operating system sandbox.
Keep the coding agent's permission controls active.

## Test the skill

Run these commands from this repository's root:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/workflow.py --help
```

The suite covers authorization boundaries, recorded answers, partial revisions, source changes, and Git records.
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
