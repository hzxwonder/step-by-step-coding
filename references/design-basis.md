# 技能设计依据

以下来源支持本技能的设计。表中的采用方式是针对逐步编程工作流的整合。它们不是原文引述，也不要求使用本技能时打开这些页面。

| 来源与类型 | 来源原则 | 本技能中的采用方式 |
|---|---|---|
| [Anthropic Prompting best practices：Overeagerness](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#overeagerness)，官方提示词 | 控制改动范围。避免无必要的检查、兜底和抽象 | 新增保护须对应真实边界或失败。内部约定已有保证时直接使用 |
| [OpenAI Skill Creator](https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md)，技能文件 | 指令只保留能改善行为的内容。细节按需展开 | 主文件保留核心规则。具体检查项和示例放在本技能的参考文件中 |
| [OpenAI Prompting Guide](https://github.com/openai/skills/blob/main/skills/.system/openai-docs/references/prompting-guide.md)，提示词指南文件 | 明确结果和成功标准。只追问会改变结果的缺失信息 | 用真实 case 明确产物。普通实现由 Agent 负责，用户决定体验与范围 |
| [GitHub awesome-copilot：Instructions](https://github.com/github/awesome-copilot/blob/main/instructions/instructions.instructions.md)，指令文件 | 从必要规则开始。根据实际问题补充约束 | 不把每种假设风险都变成代码分支或用户问题 |
| [Martin Fowler：YAGNI](https://martinfowler.com/bliki/Yagni.html)，原则阐释 | 当前不需要的能力，不因未来猜测提前实现 | 完成当前获批能力。已有明确需求和必要保护仍须完成 |
| [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)，安全指南 | 对不可信输入做语法和语义验证 | 在实际输入边界检查格式和业务规则。内部接口若跨信任边界，也须验证 |
| [Digital.gov Plain Language](https://digital.gov/guides/plain-language)，写作指南 | 根据读者需要组织内容，并检查表达是否易懂 | 先给结果和操作入口。用具体例子帮助用户作决定 |

`clear-communication.md` 采用 ASD-STE100 的结构原则。规则包括单句单意、主动表达、统一用词和保留事实强度。英文保留相应长度约束。中文按句意拆分，不套用英文词数。官方标准背景可见 [ASD-STE100](https://www.asd-ste100.org/)。

## 整合后的判定原则

代码中的保护处理须对应具体输入、已知失败或真实风险。写作中的解释须帮助读者理解、操作或决定。两者都保留当前任务的必要条件，不为缩短内容牺牲正确性。

用户表达目标。Agent 查证事实、提出建议、维护计划并提供证据。用户据此确认体验、验收结果和授权下一步。技术讲解按需展开，理解源码不是验收结果的前提。
