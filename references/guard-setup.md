# 可选的 Claude Code 代码编辑钩子

此钩子是**辅助性的拦截层**，不能替代工具本身的权限模型、独立分支、沙盒和人工 review。

## 生效范围
- 匹配 Claude Code `Write|Edit|MultiEdit|NotebookEdit` 的编辑目标路径。
- 设计阶段：允许当前任务的 `mvp-design.md`、`technical-plan.md`、`prototype.html` 与计划文档。原型用于展示体验，业务实现仍需授权。等待首次或下一步授权时，可更新这些设计产物与即将实施步骤的计划。
- 仅 `implementing` 阶段：允许改写当前步骤预先批准的文件，以及当前步骤自己的 `plan.md` / `verification.md` / `explain.md` / `preacceptance.md`。
- `precheck_setup`：可以写本步讲解、验证、预验收约定清单，仍禁止写代码。
- `precheck` 和 `precheck_discussion`：约定清单锁定，只能由状态 CLI 更新独立确认记录 `preacceptance-results.md`，不能边提问边更改已锁定选项或当前约定。
- 待验收等阶段：可补充讲解。改变计划、验证或获批文件时，须按当前授权 `revise` 并重新核对证据。讲解文字不参与实现指纹，仅补充讲解不会撤销确认。
- 验收版本检查还覆盖 MVP 设计、技术方案和产品 HTML 原型的内容及存在状态。设计变化后复核受影响证据，仍适用的需求确认可以保留。
- 下一个步骤及计划外代码永远拒绝，除非用户明确批准计划范围调整，更新允许文件名单。
- 工作流状态 `.ai-collab/**/state.json` 只通过 CLI 更新；钩子不允许普通编辑工具篡改。

## 项目级安装示例

将 `step-by-step-coding/` 放到仓库的 `.claude/skills/` 下，并在**你信任该脚本后**将以下条目合并到 `.claude/settings.local.json`（不要覆盖已有 hooks）：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit|NotebookEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python3",
            "args": ["${CLAUDE_PROJECT_DIR}/.claude/skills/step-by-step-coding/scripts/guard_edit.py"],
            "onFailure": "block"
          }
        ]
      }
    ]
  }
}
```

`onFailure: block` 需要支持它的较新 Claude Code 版本；不支持时务必自行确认钩子确实在运行。可通过 `/hooks` 和调试日志检查。

**限制：** 此钩子不会拦截 Bash 里执行的重定向、`sed`、Python 写文件、包管理器脚本、其他 MCP 工具、子 Agent 或用户在外部编辑器里的编辑。要进一步约束，请把 Shell 写操作设为人工审批，计划阶段使用 Plan/只读模式；可以在提交前做独立的 Diff 范围核查。

## 快速验证

- 在规划阶段尝试用 `Write` 写 `src/forbidden.ts`：应被拒绝。
- 在规划阶段写当前任务的 `prototype.html`：应允许；写项目正式入口 `src/app.html`：应被拒绝。
- 授权第 1 步后尝试写获批文件：应允许。
- 授权第 1 步后尝试写第 2 步文件：应被拒绝。
- 将第 1 步标记已验证后尝试修改源码：应被拒绝，需重新开放当前步骤修订。
- 启动 `start-precheck` 后尝试编辑 `preacceptance.md`：应被拒绝；如约定有歧义，先 `reset-precheck`。
