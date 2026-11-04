# 科研逐步编程

简体中文 · [English](README.md) · [MIT 许可证](LICENSE)

**用日常语言掌握研究问题、实验取舍与资源投入，通过真实结果逐步推进科研代码。**

Agent 查证已有研究材料，推荐最小实验，实现和核对当前步骤。你决定研究方向、关键比较、资源投入和是否继续。代码解释按需展开。

你可以随时了解当前研究判断，也可以核对公式、数据处理、prompt、配置、日志和结果细节。简短说明帮助你作当前决定，完整证据保留在项目文档中。
技能指令、模板和说明文档使用简体中文。

科研 MVP 默认交付可逐格运行、审查的 Jupyter Notebook。先讨论并采用路线，按可见研究进展划分步骤；短操作可在同一步内连起输入、方法与观察。先保存当前步骤并给文件链接，再补已有环境下的短测，随后结束当轮。先交付文件；用户需要网页或实时输出时，在当前任务中准备并核验页面。聊天导航摘要便于约 5 秒扫读，必要的需求讨论和结果解释充分展开。每步包含多组文本、代码与输出，段落说明它如何承接前步并服务核心 idea；每个短测代码格限时 60 秒，单格长任务或未知耗时默认交给用户手动运行。[查看可运行样例](assets/mvp.ipynb)。文件组织和展示样式由 Agent 决定，涉及科学含义、资源与权限的实际取舍再提问。

Agent 恢复研究进度，接续你的上一反馈，说明本步问题、关键做法和它对核心 idea 的作用。已有科学与资源决定沿用，真正未决需求再讨论。Notebook 用多组短文本与代码实现同一个步骤；核心图组旁解释数值如何得到、为何如此、支持或限制哪项判断，必要推理保留在对应位置。

## 它能帮你做什么

- 用具体样例一次讨论一个核心决定，说明它对结果、范围或成本的影响。
- 决定变化时更新当前设计，复用已采用的方法、对照、数据、指标、判定规则与预算。
- 先确定当天步骤，每轮保存并交付一个 Notebook 步骤，让用户阅读、执行和反馈。
- 在阶段交付时说明当前子问题、已知事实与推测，以及下一项实验为何值得做。
- 将关键约定连到检查和真实证据，按改动选择测试或实际操作。
- 用统一的研究名称、公式与代码对应和按需解释降低理解负担。
- 记录确认来源与范围，保留仍适用的决定，分别登记授权和验收。
- 展示当前真实 case，区分执行有效性、科学判断与用户接受，沿用用户的教学与验收节奏，按 Git 约定保存。

可信负结果也可完成当前里程碑，代码运行成功和测试通过不等于假说得到支持。理解问题用于帮助解释观察，不是验收前提。
修改后，agent 验证受影响的实现，只补充确认新增、变化或尚未解决的行为。
你已明确要求的行为，在实现并验证后可直接按原话记录，无需再问一次。

## 对话会怎样进行

agent 每轮先讲一个与你当前操作相关的重点，完整证据放在项目文档里供按需阅读。
需要你决定时，它先说明实际做法和建议。只有存在真实取舍时才给其他方案。
你可以直接说自己的想法，也可以让它先举例，不需要回答字母。

例如：**这一步先比较整体效果，还是验证某个机制？** 这会改变对照和观察指标。
agent 会把决定连到公式、代码和评测规则，解释改动如何影响结论。
你觉得内容太多时，它会用当前 case 简短说明，再按需展开。已有有效检查直接复用。首步先交付一条服务核心问题的可执行路径，说明与后续范围按反馈展开。

[中文 Notebook 写作约定](references/notebook-cells.md#中文结果与图表)明确术语、指标分母与比较口径，区分百分点和相对变化，并分别表达未运行、执行失败及证据不足。图表标明单位、对照和统计含义，真实不确定性用具体缺口说明。

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
$step-by-step-coding 帮我根据当前实验包完成 MVP。我是科研初学者。
沿用核心 idea、已采用协议和有效结果，让 Notebook 从基本概念讲起，用实例、图解和短代码逐步实现核心方法，再讲清对照与观察。
```

使用 Claude Code 时，将开头改为 `/step-by-step-coding`。

Agent 先恢复已采用设计、预算与有效结果，再安排后续比较。Notebook 使用自然中文，每段先说用途和要看的变化，技术术语首次用日常话解释；实验 ID、哈希、审批和管理清单留在项目记录。需要用户作取舍的未决项应影响假说、公平性、权限或主要成本；阅读疑问和结果解释按当前需要展开。

Agent 每轮完成一个采用的步骤，内部按理解任务分成多个文本与代码块。步首先说明承接关系和当前证据缺口，步尾解释已回答什么及下步作用；聊天给出针对观察、目标场景或解释的反馈入口。修改意见原位整合，“继续”推进下一采用步骤；每格不另设审批。

| 你发送的消息 | 会怎样推进 |
|---|---|
| `按当前方案开始` | 沿用已采用路线，实现并交付当前步骤；按短测或手动运行方式执行。 |
| `继续` | 推进下一个采用步骤；缺少手动结果时指出需要运行的单元。 |
| `解释一下这段代码` | 解释当前实现或 case。 |
| `把这个对照换成……` | 先核对对研究问题、公平性与成本的影响，再调整比较。 |
| `本轮符合预期` | 在实际范围内登记对已展示结果的接受。 |

这些是示例，不是必须复述的口令。Agent 保留决定的来源与范围，资源授权与逐轮交付分别维护。“继续”不补造科学支持或正式验收；新增费用、权限或超出已采用科学范围的变化仍需相应决定。

只自动运行已授权且已知短的本步内容，每个短测代码格限时 60 秒；单格长任务或时长未知的单元默认交给用户手动运行。准备与探测仅处理本步实际阻碍。优先复用 SDK、评测工具、原始回包与简洁日志；元数据未知仅在影响当前比较或真实资源、权限边界时阻断。缺少成本证据时收窄成本主张，保留其它有效观察。MVP 结论限于实测范围，正式实验再满足采用评测协议的样本、重复和统计要求。

## 项目中会生成什么

Notebook 教学采用紧凑布局：

```text
mvp.ipynb              # 设计、可读实现、观察与复现方式
.research/session.md   # 采用来源、决定、当前里程碑和剩余工作
evidence/              # 按需要保存原始结果和日志
```

已有协议和结果保持原事实来源。修改原位整合，每轮给出文件和已有真实网址。默认复用已知环境与已核验页面，环境不可用时交付待运行代码。纯文字修改保留代码与实测输出，保存后直接交付。图后分析讲清关键数值的来源、机制与证据作用；变化数值由代码输出，文字保留必要推理。后续方案采用后细化。

明确启用状态脚本的项目，沿用 `docs/ai-collab/<task>/` 记录与 `.ai-collab/` 状态。模板位于 `assets/`，详见[约定记录指南](references/alignment-mcq.md)。状态反映实际决定和证据，不产生授权、验收或额外审查阶段；用户明确要求的暂停与验收节点仍须遵守。

个人回答和工作流状态保留本地。使用状态脚本的项目提交前，将以下内容加入该项目的 `.gitignore`：

```gitignore
.ai-collab/
**/preacceptance-results*.md
```

本 skill 仓库的忽略规则不会自动配置另一个项目。

## 可选的状态脚本

agent 可以使用 `scripts/workflow.py` 记录实际决定并检查记录的阶段转换。
你可以全程通过对话使用 skill，无需亲自输入这些状态命令。

在本 skill 仓库根目录查看帮助：

```bash
python3 scripts/workflow.py --help
```

执行状态命令时，将 `--repo` 放在命令前，用它指定真正要管理的项目：

```bash
python3 scripts/workflow.py --repo /path/to/your-project status
```

`status` 需要已初始化的脚本任务；对话模式无需初始化。
脚本检查记录结构，Agent 核对实际授权、科学含义与真实证据；脚本不执行实现测试或推送提交。
来源、范围、case 展示与证据按实际情况登记。状态转换不能表达已授权比较时，保留原状态并在 Notebook 记录进展，不补造接受来解锁。
变化后只复核受影响证据，仍适用的确认沿用，详见[行为验证方法](references/behavior-verification.md)。

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
