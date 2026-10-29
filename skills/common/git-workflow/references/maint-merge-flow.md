# Maintenance Branch Merge Workflow

## Required Inputs

- `target_branch`: the maintenance/release branch to receive the feature branch, such as `drama-ios_2.22.0_maint`.
- `feature_branch`: the feature branch to merge, such as `feat/1001752_family_sign`.
- `remote`: default to `origin`, but confirm it from the repository before pushing.

If the user only asks to continue an interrupted flow, infer the current step from `git status` and branch state. Ask for missing branch names only when they cannot be inferred safely.

## Main Workflow

1. Inspect state:
   - Run `git status --short --branch`.
   - Run `git remote -v` if the remote is not already certain.
   - Confirm `target_branch`, `feature_branch`, and `remote`.
   - Do not proceed when unrelated user changes are present until the user confirms how to handle them.

2. Update the target branch:
   - Run `git switch <target_branch>`.
   - Run `git pull --rebase <remote> <target_branch>`.

3. Rebase the feature branch onto the updated target:
   - Run `git switch <feature_branch>`.
   - Run `git rebase <target_branch>`.
   - Follow "Rebase Conflict Handling" if conflicts occur.

4. Merge the feature branch into the target branch:
   - Run `git switch <target_branch>`.
   - Run `git merge <feature_branch> --no-ff`.
   - Preserve Git's merge-commit message; the normal code-commit convention does not apply.
   - Follow "Merge Conflict Handling" if conflicts occur.

5. Verify and push the target branch:
   - Run `git status --short --branch`.
   - Run `git log --oneline --graph --decorate -n 20`.
   - Confirm that the current branch is the target, no rebase or merge is unfinished, no conflicts remain, and the graph matches the intended merge.
   - If the graph and worktree are correct, run `git push <remote> <target_branch>`.

6. Sync the feature branch to the merged target:
   - Run `git switch <feature_branch>`.
   - Run `git rebase <target_branch>`.
   - Follow "Rebase Conflict Handling" if conflicts occur.

7. Verify completion:
   - Run `git status --short --branch`.
   - Run `git log --oneline --graph --decorate -n 20`.
   - Report the target branch, feature branch, pushed remote, validation, conflicts handled, and whether the feature branch is aligned with the target.

## Rebase Conflict Handling

- Run `git status` to confirm the rebase state and list conflicted files.
- Inspect conflicts with `git diff` and search for markers with `rg "<<<<<<<|=======|>>>>>>>"`.
- Resolve only conflicts whose intent is clear from surrounding code and repository rules.
- Ask the user before resolving a conflict that changes business behavior, API semantics, compatibility, state retention, or another user-owned decision.
- After resolving conflicts, run `git add <resolved-files>` and `git rebase --continue`.
- Repeat until the rebase finishes.
- Run `git rebase --abort` only when the user explicitly asks to abandon the rebase.

## Merge Conflict Handling

- Run `git status` to confirm the merge state and list conflicted files.
- Inspect conflicts with `git diff` and `rg "<<<<<<<|=======|>>>>>>>"`.
- Resolve only conflicts whose intent is clear.
- Ask the user before choosing between target-branch and feature-branch behavior.
- After resolving conflicts, run `git add <resolved-files>` and `git commit` to finish the merge commit.
- Run `git merge --abort` only when the user explicitly asks to abandon the merge.

## Resume After User-Resolved Conflicts

- Run `git status` first.
- If a rebase is active, verify that no unresolved markers remain, stage the resolved files explicitly, and run `git rebase --continue`.
- If a merge is active, verify that no unresolved markers remain, stage the resolved files explicitly, and run `git commit`.
- If neither operation is active, inspect the branch and recent graph to infer the next unfinished workflow step.
- If the next step cannot be inferred safely, report the current state and ask the user which step to resume.

## Completion Criteria

- The target branch contains the feature branch through a `--no-ff` merge commit.
- The target branch is pushed to the intended remote.
- The feature branch is rebased onto the updated target after the merge.
- `git status --short --branch` shows no unfinished rebase, merge, or unresolved conflicts.
- Validation follows repository rules. For drama-ios, do not proactively run builds, compilers, or SDK discovery commands; use only permitted static checks.
