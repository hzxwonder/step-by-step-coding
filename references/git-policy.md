# GitHub / GitCode 可选推送策略

## 权限和询问顺序（一次一问）
1. 总计划已批准，但**首次业务代码尚未开始时**问：“每个步骤验收后需要推送 GitHub / GitCode，还是仅保留本地？”
2. 若答“需要”，下一轮问“GitHub 还是 GitCode？”
3. 之后问目标**已存在**仓库是哪个（准确 URL 或 remote 名称；不要自行创建仓库）。
4. 再确认推送分支名称。默认建议创建独立功能分支，比如 `feature/<task-slug>`；保护分支需要额外明确批准。
5. 核对 `git remote -v`、当前分支、用户当前改动，先检查是否有敏感信息及团队协作约束。
6. 用户必须知道每个**已验收**步骤或再次验收的修订会自动执行一次 commit/push。若不接受，请使用本地模式。

## 每步验收后的安全工作流（在当前步骤内）
- 确认测试通过，`verification.md` 有真实证据，`explain.md` 已经讨论、4–6 道需求对齐选择题全部确认一致且用户明确正式验收。
- `git status --short`、`git diff --stat`、`git diff`，同时查看未跟踪文件；禁止将用户无关文件一起上传。
- 重点检查 `.env`、token、密钥、账号、私有记录、数据集、生成文件、`.ai-collab/**/state.json` 和 `.ai-collab/active.json`、`preacceptance-results.md`（可能包含用户原话）以及 `preacceptance-results-old-*.md`；这些本地状态/回答默认建议 `.gitignore`，不要推送。
- 仅对**已获批改动列表和本次步骤文档**执行精确 `git add path1 path2 ...`（不用 `git add .`、`git add -A`）。`git diff --cached` 再核对一次。
- 用本步骤的说明提交新的 commit，如 `feat(step-01): 保存一笔账目`。
- 运行 `git push <confirmed-remote> HEAD:<confirmed-branch>`（首次按需要建立 upstream）。GitHub、GitCode 都使用 Git 远程模型，但必须使用用户真实配置的仓库 URL，不要猜测。
- 确认 Git 命令返回码为 0，并记录 commit SHA、remote/branch、成功/失败。
- 若失败，报告错误、暂停，不擅自 `--force` / `--force-with-lease` / 换 remote / 改历史 / merge / rebase / 删除远端分支。
- 推送成功后**也不**自动进入下一步。

## 额外限制
- 不要求用户在聊天中粘贴密码、token 或 SSH 私钥。使用 `gh auth` / Git credential helper / SSH Agent 等已配置的本地授权。
- 不自动创建公开仓库，不修改公开可见性或仓库访问策略。
- 若目标为 `main`/`master` 或有保护规则，单独告知风险并要求明确批准；更推荐功能分支。
- 若从零开始、仓库尚未初始化，只在用户同意 Git 工作流后讨论 `git init` 和 remote 配置，不能在最初需求访谈中擅自操作。
- 按用户要求在已验收步骤修改后，可以产生新 commit 再 push；**禁止对已推送的 commit amend 后强推**。
