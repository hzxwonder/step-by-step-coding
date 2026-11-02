# 科研逐步编程

简体中文 · [English](README.md) · [MIT 许可证](LICENSE)

**用日常语言掌握研究问题、实验取舍与资源投入，通过真实结果逐步推进科研代码。**

Agent 查证已有研究材料，推荐最小实验，实现和核对当前步骤。你决定研究方向、关键比较、资源投入和是否继续。代码解释按需展开。

你可以随时了解当前研究判断，也可以核对公式、数据处理、prompt、配置、日志和结果细节。简短说明帮助你作当前决定，完整证据保留在项目文档中。
技能指令、模板和说明文档使用简体中文。

科研 MVP 默认交付可逐格运行、审查的 Jupyter Notebook。[查看可运行样例](assets/mvp.ipynb)。文件组织和展示样式由 Agent 决定，涉及科学含义、资源与权限的实际取舍再提问。

## 它能帮你做什么

- 用具体样例一次讨论一个核心决定，说明它对结果、范围或成本的影响。
- 逐轮返回最小实验设计，说明方法、对照、数据、指标、判定规则与预算，并形成实现方案。
- 设计获认可并取得授权后，尽早跑通实际输入、方法与对照、日志与结果，再按证据需要扩展。
- 在阶段交付时说明当前子问题、已知事实与推测，以及下一项实验为何值得做。
- 将关键约定连到检查和真实证据，按改动选择测试或实际操作。
- 用统一的研究名称、公式与代码对应和按需解释降低理解负担。
- 记录确认来源与范围，保留仍适用的决定，分别登记授权和验收。
- 验收前展示真实 case，分别记录执行有效性、科学判断与用户验收，按 Git 约定保存。

预验收核对实现和实验是否符合约定，可信负结果也可完成交付。代码运行成功和测试通过不等于假说得到支持。
修改后，agent 验证受影响的实现，只补充确认新增、变化或尚未解决的行为。
你已明确要求的行为，在实现并验证后可直接按原话记录，无需再问一次。

## 对话会怎样进行

agent 每轮先讲一个与你当前操作相关的重点，完整证据放在项目文档里供按需阅读。
需要你决定时，它先说明实际做法和建议。只有存在真实取舍时才给其他方案。
你可以直接说自己的想法，也可以让它先举例，不需要回答字母。

例如：**这一步先比较整体效果，还是验证某个机制？** 这会改变对照和观察指标。
agent 会把决定连到公式、代码和评测规则，解释改动如何影响结论。
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
$step-by-step-coding 帮我验证这个研究模块是否有效。我是科研初学者。
先接续已有协议，讨论最小实验、对照、指标和预算，再按认可与授权逐步实现。
```

使用 Claude Code 时，将开头改为 `/step-by-step-coding`。

Agent 每轮设计讨论后更新并返回最小实验设计。已有研究协议直接引用，默认用实验表、样本和结果字段帮助决定；实际需要交互工具时再提供 HTML 原型。
你可以一次认可设计、技术方案、路线并授权第一步。后续步骤先保留概要，轮到实施时再细化。
默认只保留本地。你要求远程备份时，再补齐目标与分支。
实际 prompt、生效配置、完整真实日志和产物按需要作为同一次运行的证据。

接下来可以按阶段发送这些消息：

| 你发送的消息 | 允许做什么 |
|---|---|
| `确认需求，生成计划` | 生成总计划和各步骤计划。 |
| `认可刚展示的实验设计、技术方案和计划` | 认可相应设计与计划，尚未启动实施。 |
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
├── prototype.html  # 有明确交互需求时提供
└── steps/01-step/
    ├── plan.md
    ├── verification.md
    ├── explain.md
    ├── preacceptance.md
    └── preacceptance-results.md

.ai-collab/<task>/state.json
.ai-collab/active.json
```

`mvp-design.md` 保存最小实验、判定与资源边界。`technical-plan.md` 保存实现来源、数据流与评测入口。
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

新任务默认 `research`，计划批准检查核心闭环、研究问题、判定规则、资源边界与实现方案。后续步骤在各自授权前补细节；已有任务沿用原有约定。
脚本检查基础结构；比较是否合理、证据是否充分与自然语言授权，仍由 Agent 根据实际材料和对话核对。

验收版本检查覆盖最小实验设计、实现方案与按需 HTML 原型，检测内容变化、新建或删除。
变化后复核受影响证据，仍适用的确认沿用。测试与实际操作的选择见[行为验证方法](references/behavior-verification.md)。

`verified --result pass` 登记执行与证据核对有效。`--finding supports|does-not-support|inconclusive|not-assessed` 单独记录科学判断，默认本步未评估。实现或评测错误保留未通过状态，有效负结果可以验收。

明确的软件任务由 Agent 选择 `init --focus software`，无需额外询问任务类型。科研设计和实验记录方法见[研究工作流](references/research-workflow.md)。

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
