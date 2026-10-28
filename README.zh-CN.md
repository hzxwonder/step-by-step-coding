# 逐步编程

简体中文 · [English](README.md) · [MIT 许可证](LICENSE)

**用日常语言表达目标，通过样例和真实运行决定结果，掌握开发范围与节奏。**

Agent 负责查证、推荐、实现和验证。你决定关键行为、接受当前结果，并授权下一步。代码讲解按需阅读。

你可以随时了解整体进度，也可以核对界面、prompt、配置和结果细节。简短说明帮助你作当前决定，完整证据保留在项目文档中。
技能指令、模板和说明文档使用简体中文。

## 它能帮你做什么

- 用具体样例一次讨论一个核心决定，说明它对结果、范围或成本的影响。
- 逐轮返回简短 MVP 设计，产品提供可修改的 HTML 原型，并形成技术方案。
- 设计获认可并取得启动授权后，尽早跑通核心流程，后续步骤逐次改善可用版本。
- 在阶段交付时说明整体进展、已可用结果与下一项成果。
- 将关键约定连到检查和真实证据，按改动选择测试或实际操作。
- 用业务名称、直白代码和按需讲解降低理解负担。
- 记录确认来源与范围，保留仍适用的决定，分别登记授权和验收。
- 验收前展示当前版本的真实 case，按已确认的 Git 策略保存结果。

预验收用于核对“系统是否按你希望的方式工作”，不考术语或代码记忆。
修改后，agent 验证受影响的实现，只补充确认新增、变化或尚未解决的行为。
你已明确要求的行为，在实现并验证后可直接按原话记录，无需再问一次。

## 对话会怎样进行

agent 每轮先讲一个与你当前操作相关的重点，完整证据放在项目文档里供按需阅读。
需要你决定时，它先说明实际做法和建议。只有存在真实取舍时才给其他方案。
你可以直接说自己的想法，也可以让它先举例，不需要回答字母。

例如：**再次保存时，你希望替换旧记录，还是把旧记录也保留下来？**
agent 会把你的决定连到相关代码，解释改动如何影响使用结果。
你觉得内容太多时，它会先缩小到一个具体例子，再逐步展开。

## 使用前准备

- 支持 skill 的本地 Codex 或 Claude Code 环境。
- Git：用于安装，以及可选的版本保存流程。
- Python 3.9 或更新版本：用于可选状态脚本和测试。
- 能访问你准备开发的项目目录。

Python 脚本只使用标准库，无需安装额外 Python 包。
本仓库提供独立 skill 文件夹，不含插件清单或 MCP 服务。

## 安装

根据你的工具选择一个安装位置。以下命令适用于 macOS 或 Linux 终端。
目标目录需要尚未存在。

### Codex：在自己的所有本地项目中使用

```bash
mkdir -p "$HOME/.agents/skills"
git clone https://github.com/hzxwonder/step-by-step-coding.git "$HOME/.agents/skills/step-by-step-coding"
```

只在一个项目中使用时，在该项目根目录执行：

```bash
mkdir -p .agents/skills
git clone https://github.com/hzxwonder/step-by-step-coding.git .agents/skills/step-by-step-coding
```

Codex 会自动发现技能变化。未出现时，重新启动 Codex。
在 Codex CLI 或 IDE 扩展中，输入 `/skills`，或输入 `$` 选择该技能。
安装目录和发现机制以 [OpenAI 官方文档](https://learn.chatgpt.com/docs/build-skills)为准。

如果你的 Codex 已提供 `$skill-installer`，也可以在对话中输入：

```text
$skill-installer 请从 GitHub 安装 hzxwonder/step-by-step-coding。
仓库内路径为 .，技能名为 step-by-step-coding。
```

安装器使用它配置的技能目录。需要指定位置时，使用上面的手动命令。

### Claude Code：在自己的所有本地项目中使用

```bash
mkdir -p "$HOME/.claude/skills"
git clone https://github.com/hzxwonder/step-by-step-coding.git "$HOME/.claude/skills/step-by-step-coding"
```

只在一个项目中使用时，将复制目标设为 `.claude/skills/step-by-step-coding`。
Claude Code 通常会检测技能文件的变化。
如果在当前会话中新建了技能目录，技能未出现时可执行 `/reload-skills`。
详见 [Claude Code 官方说明](https://code.claude.com/docs/en/skills)。

## 开始第一个任务

在你的编程工具中打开准备开发的项目，然后在 Codex 对话框输入：

```text
$step-by-step-coding 帮我做一个本地记账工具。我是初学者。
先用具体例子对齐结果，给出建议，再按批准的步骤实施。
```

使用 Claude Code 时，将开头改为 `/step-by-step-coding`。

Agent 每轮设计讨论后更新并返回 MVP 设计。技术方案与产品原型帮助你作决定。
你可以一次认可设计、技术方案、路线并授权第一步。后续步骤先保留概要，轮到实施时再细化。
默认只保留本地。你要求远程备份时，再补齐目标与分支。
实际 prompt、生效配置、完整真实日志和产物按需要作为同一次运行的证据。

接下来可以按阶段发送这些消息：

| 你发送的消息 | 允许做什么 |
|---|---|
| `确认需求，生成计划` | 生成总计划和各步骤计划。 |
| `认可刚展示的 MVP 设计、技术方案和计划` | 认可相应设计与计划，尚未启动实施。 |
| `开始第 1 步` | 按获批计划实施第一步。 |
| `解释一下这段代码` | 讲解当前实现。 |
| `开始预验收` | 核对关键约定，只询问尚未解决的决定。 |
| `本步骤验收通过` | 在行为对齐后正式验收当前步骤。 |
| `开始第 2 步` | 单独授权实施下一步。 |

上面的消息是示例，不是必须复述的口令。
行为确认后，你明确说“这一步符合我的预期，就这样”，也可以表达对当前步骤的认可。
agent 结合上下文理解并记录你的真实原话。

批准计划、验收当前步骤、启动下一步是三个独立决定。
同一句话明确包含多个决定时，Agent 可分别记录，无需分轮重复确认。单个决定不自动代表其他许可。

## 项目中会生成什么

以下文件保存在你正在开发的项目中：

```text
docs/ai-collab/<task>/
├── plan.md
├── mvp-design.md
├── technical-plan.md
├── prototype.html  # 产品设计时提供
└── steps/01-step/
    ├── plan.md
    ├── verification.md
    ├── explain.md
    ├── preacceptance.md
    └── preacceptance-results.md

.ai-collab/<task>/state.json
.ai-collab/active.json
```

`mvp-design.md` 保存主要功能和本轮取舍。`technical-plan.md` 保存技术栈、理由与运行方式。
`plan.md` 定义首次可用步骤及后续路线。`verification.md` 记录实际验证。
`explain.md` 供按需阅读。`preacceptance.md` 保存关键约定与证据。
回答记录保存你的选择，`.ai-collab` 文件保存工作流状态。

个人回答和工作流状态保留在本地。提交前，在目标项目的 `.gitignore` 中加入：

```gitignore
.ai-collab/
**/preacceptance-results*.md
```

本 skill 仓库的忽略规则不会自动配置另一个项目。

## 可选的状态脚本

agent 可以使用 `scripts/workflow.py` 记录真实授权并检查阶段转换。
你可以全程通过对话使用 skill，无需亲自输入这些状态命令。

在本 skill 仓库根目录查看帮助：

```bash
python3 scripts/workflow.py --help
```

执行状态命令时，将 `--repo` 放在命令前，用它指定真正要管理的项目：

```bash
python3 scripts/workflow.py --repo /path/to/your-project status
```

`status` 需要先初始化任务。批准规划工作时，可以让 agent 初始化工作流。
脚本不会替你执行实现测试、判断自然语言回答或推送提交。
agent 需要实际运行检查，再记录证据。

确认记录须提供来源类型、原话位置和适用范围。脚本拒绝将授权或 Agent 自选类型登记为需求确认。验收前还需登记真实 case 的展示位置与实际证据文件。语义范围及证据真实性仍由 Agent 根据上下文和实际运行核对。

计划批准检查 MVP 核心闭环、技术方案和首次可用步骤。后续步骤在各自授权前补齐细节。
脚本只检查基础结构；功能取舍、设计认可和产品原型是否充分，仍由 Agent 根据实际对话核对。

验收版本检查覆盖 MVP 设计、技术方案和 HTML 原型，能检测内容变化、新建或删除。
变化后复核受影响证据，仍适用的确认沿用。测试与实际操作的选择见[行为验证方法](references/behavior-verification.md)。

[Claude Code 可选钩子示例](references/guard-setup.md)只能检查指定的编辑工具。
它无法覆盖 Shell 写操作和所有其他工具，也不是操作系统沙盒。
继续使用编程工具本身的权限控制。

## 验证 skill

在本 skill 仓库根目录执行：

```bash
python3 -m unittest discover -s tests -v
python3 scripts/workflow.py --help
```

测试覆盖授权边界、确认记录、设计与源码变化、局部修订和 Git 记录，也检查编辑守卫的路径判定。
发布检查包含 macOS 上的运行。仓库的 GitHub 工作流在 Ubuntu、Python 3.11 上执行测试。
Claude Code 钩子的真实集成和 Windows 执行需要单独验证。

## 更新或卸载

对于上面的 Codex 用户级 Git 安装方式，执行：

```bash
git -C "$HOME/.agents/skills/step-by-step-coding" pull --ff-only
```

其他安装位置使用对应目录。若 Git 提示本地修改或历史分叉，先保留自己的修改，再处理更新。
安装器创建的目录可能不含 Git 历史，请按安装器说明更新。

卸载时，将已安装的 `step-by-step-coding` 文件夹移出技能发现目录，再刷新工具的技能列表。
你仍需使用的项目计划和记录可以保留。

## 仓库结构

| 路径 | 用途 |
|---|---|
| [SKILL.md](SKILL.md) | agent 读取的技能指令。 |
| [agents/openai.yaml](agents/openai.yaml) | Codex 中的显示名称与示例提示词。 |
| [scripts/](scripts/) | 状态脚本和可选编辑守卫。 |
| [references/](references/) | 工作流规则与配置示例。 |
| [assets/](assets/) | 计划、验证、讲解和预验收模板。 |
| [tests/](tests/) | 使用 Python 标准库的测试。 |

[仓库发布调研](docs/repository-study.zh-CN.md)说明参考项目、安装依据与采用的结构。
两份 README 参考 [ASD-STE100](https://www.asd-ste100.org/) 的短句、直接指令与统一术语原则。
英文按这些原则编写，中文采用对应的清晰表达方式。文档不宣称通过正式 STE 认证。

## 许可证

[MIT](LICENSE)。Copyright 2026 hzxwonder。
