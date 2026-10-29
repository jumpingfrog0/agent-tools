# Likee 本地提交规范

先完成 SKILL.md 中的执行前检查，再按当前仓库规则执行以下步骤。


1. 检查 `git diff --cached`、`git diff`，确定用户授权的文件范围。只提交暂存区时，不额外暂存文件。
2. 按当前仓库 `.cursor/rules/commit.mdc` 生成提交信息，保留用户指定的分支名、信息和 Change-Id。不套用其他项目的类型或需求号规则。
3. 仅以明确路径暂存授权改动；检查 `git diff --cached --stat` 和完整 staged diff，避免空提交或夹带改动。
4. 运行仓库要求且用户允许的验证及 `git diff --cached --check`。格式检查不等于编译或运行验证。
5. 执行普通 `git commit`，不隐式 amend，不使用 `--no-verify`。多行信息写临时文件并用 `git commit -F <message-file>`。
6. 用 `git show --stat --oneline -1` 和 `git status --short --branch` 验证。仓库要求 git-ai 归因时检查 `git notes --ref=ai show HEAD`，如无 note 如实报告。
7. 仅要求提交时完成本地提交即停止，不自动 rebase 或推送。

