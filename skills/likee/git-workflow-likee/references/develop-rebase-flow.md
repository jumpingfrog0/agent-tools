# Develop Rebase 流程

先完成 SKILL.md 中的执行前检查。默认将功能分支 rebase 到更新后的 develop；完成后不自动 merge 或 push。

## 功能分支同步


确认分支名后逐步执行以下命令；每步成功后才能进入下一步。`<feature_branch>` 必须替换成已确认的实际分支名。

```bash
git switch develop
git pull --rebase origin develop
git switch <feature_branch>
git rebase develop
git status --short --branch
git log --oneline --graph --decorate -n 20
git merge-base --is-ancestor develop <feature_branch>
```

- `git pull --rebase` 若失败或冲突，先处理当前步骤，不能拿未更新的 develop 继续。
- 本地 develop 若有远端没有的提交，先检查并告知这些提交也会成为 rebase 基底；若含义或归属不明，先让用户决定，不擅自丢弃。
- 完成时停留在功能分支，确认 develop 是其祖先、工作区干净、无进行中的 rebase 或未解决冲突。
- 不继续 merge，不自动 push，也不运行通用流程的「合并后同步」。用户另有明确推送指令时再处理；rebase 后不能擅自强推。

## 冲突与中断恢复

先用 `git status` 判断实际状态，不重复启动 rebase。

```bash
git status
git diff
git diff --name-only --diff-filter=U
```

仅解决意图明确的冲突；涉及业务行为、API 语义、兼容性、状态保留等取舍时让用户决定。解决后检查相关文件的冲突标记，仅暂存明确解决的文件：

```bash
git add <resolved-files>
git rebase --continue
```

重复直到完成，然后从中断步骤之后继续。仅在用户明确要求放弃时运行 `git rebase --abort`；不以 `--skip` 静默丢弃提交。若发现正在 merge，报告状态并确认如何继续，不把它当成本技能的自动步骤。

