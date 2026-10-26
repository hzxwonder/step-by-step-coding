# Skill 仓库结构与使用说明调研

核验日期：2026-10-26。采用结构：独立 Agent Skill 仓库，根目录为技能入口。

## 参考项目

| 项目 | 分发方式 | 本项目采用的做法 |
|---|---|---|
| [openai/skills](https://github.com/openai/skills) | 多技能集合，包含技能安装器 | 展示技能目录、脚本与明确安装入口。安装路径以当前官方文档为准。 |
| [anthropics/skills](https://github.com/anthropics/skills) | 技能集合与 Claude 插件市场 | 分别说明文件夹安装与插件分发。本项目提供文件夹安装。 |
| [obra/superpowers](https://github.com/obra/superpowers) | 多技能工作流，按工具提供安装入口 | 将使用流程、批准边界和工具差异写清楚。 |
| [vercel-labs/skills](https://github.com/vercel-labs/skills) | 第三方技能管理 CLI | 在 README 中提供安装、发现、更新和卸载说明。 |

这是结构与文档参考，不是对上述项目功能的复刻。第三方 CLI 安装不属于本项目已验证的安装路径。

## 仓库结构

[Agent Skills 规范](https://agentskills.io/specification)要求 `SKILL.md`，并要求 YAML 中包含 `name` 与 `description`。
`scripts/`、`references/` 和 `assets/` 是可选的支持目录。
因此，本项目的 Git 仓库本身就是一个技能文件夹，安装时直接复制或克隆到发现目录。
README 面向安装者，`SKILL.md` 面向 agent。两者承担不同作用。

## 安装依据

| 工具 | 用户级目录 | 项目级目录 | 显式调用 |
|---|---|---|---|
| Codex | `~/.agents/skills/step-by-step-coding` | `.agents/skills/step-by-step-coding` | `$step-by-step-coding` |
| Claude Code | `~/.claude/skills/step-by-step-coding` | `.claude/skills/step-by-step-coding` | `/step-by-step-coding` |

[OpenAI 官方文档](https://learn.chatgpt.com/docs/build-skills)说明上述 Codex 目录、自动发现和重启回退方法。
它也建议将面向更多用户的复用分发打包为插件。当前交付提供本地文件夹安装，未声明为插件市场包。
[Claude Code 官方文档](https://code.claude.com/docs/en/skills)说明其技能目录、调用和 `/reload-skills` 行为。
[钩子参考](https://code.claude.com/docs/en/hooks)用于核验可选编辑守卫配置。
本项目仅在明确列出的环境完成实际检查，目录兼容说明不代表所有工具集成都已实测。

## README 的信息顺序

1. 说明用途、面向人群和默认语言。
2. 列出 Git、Python 与工具前提。
3. 按工具与作用域给出复制即可运行的安装命令。
4. 给出完整提示词和真实阶段消息。
5. 解释计划、验证、讲解、确认题与本地状态文件。
6. 说明用户授权、局部修订和 Git 推送的边界。
7. 给出测试命令、已验证范围与尚需单独验证的集成。
8. 说明更新、卸载和 MIT 许可证。

## 文档写法

参考 [ASD-STE100](https://www.asd-ste100.org/)：一条指令只表达一个动作，优先使用主动语态、短句和统一术语。
英文不复制官方词典，也不宣称正式认证。中文采用相同的清晰表达目标。
实际状态脚本、技能元数据和 README 示例需要相互一致。
