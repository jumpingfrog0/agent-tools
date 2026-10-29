---
name: git-workflow-likee
description: 执行 Likee 项目的本地提交与 develop 同步流程。用于提交代码、将功能分支 rebase 到最新 develop、继续中断的 rebase；rebase 完成即停止，不自动 merge 或 push。
---

# Likee Git Workflow

## 路由与边界

- 提交代码：完整读取并执行 [Likee 提交规范](references/commit-conventions.md)。
- 同步 develop / rebase：完整读取并执行 [develop rebase 流程](references/develop-rebase-flow.md)。若同时要求提交，先完成本地提交。
- 本技能不采用通用 git-workflow 的自动 merge、推送目标分支、合并后同步流程。功能分支 rebase 完成即停止，不自动 merge 或 push。
- 不自动执行 `git merge`，不自动将功能提交合入或推送到 develop。单独明确要求合并时，按仓库流程另行处理，不从 rebase 请求推断合并授权。
- 默认方向是「功能分支 rebase 到 develop」。用户明确指定其他方向时遵从其指令，先说明将被移动的分支与基底；有歧义时先澄清，不擅自反转。

## 执行前检查

1. 先运行 `git status --short --branch`，读取仓库 `AGENTS.md` 与 `.cursor/rules/` 中适用的编码、提交规则。
2. 用 `git branch --show-current`、`git remote -v`、`git worktree list` 确认功能分支、远端及 worktree 占用。默认远端为 origin，目标为 develop；功能分支不能凭空猜测。若当前是 develop，且上下文不能确定功能分支，先询问。
3. 保留用户改动，不隐式 stash、丢弃、reset 或暂存无关文件。工作区不干净且会影响切分支或 rebase 时，停下让用户决定如何处理。
4. 不绕过 hooks；按仓库要求使用 Git 写权限。推送、强推、amend 均需用户明确要求。

## 完成报告

说明实际方向、最终分支和 HEAD、develop 更新情况、冲突处理、验证及其限制、是否推送。明确区分 rebase 完成与合入 develop；本流程完成不代表已合并或发布。
