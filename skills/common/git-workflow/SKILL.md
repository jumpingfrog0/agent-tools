---
name: git-workflow
description: "Perform safe Git delivery workflows: create scoped local commits that follow repository conventions, or merge a feature branch into a maintenance/release branch through update, rebase, --no-ff merge, push, post-merge sync, and conflict recovery. Use when the user asks to commit code or changes, prepare a repository-compliant commit message, merge a feature branch into a maint/release branch, run the rebase + no-ff merge flow, sync the feature branch after a maint merge, or continue an interrupted rebase/merge."
---

# Git Workflow

## Route the Request

- For a normal code commit or commit-message request, read [references/commit-conventions.md](references/commit-conventions.md) completely and follow it.
- For a feature-to-maintenance/release branch merge or an interrupted rebase/merge, read [references/maint-merge-flow.md](references/maint-merge-flow.md) completely and follow it.
- When the user explicitly requests both operations, complete the commit workflow first, then start the maintenance merge workflow.
- Do not run the maintenance merge workflow merely because the user asks to commit code.

## Shared Safety Rules

- Start with `git status --short --branch` and inspect repository instructions before mutating Git state.
- Preserve unrelated user changes. Never stage, stash, discard, reset, or rewrite them implicitly.
- Use explicit branch names and file paths. Do not rely on shell aliases.
- Do not run destructive commands such as `git reset --hard`, `git checkout -- <file>`, recursive deletion, or bulk deletion unless the user explicitly requests that exact operation.
- Never bypass hooks with `--no-verify`.
- Do not push, force-push, amend, rebase, or merge unless the selected workflow or the user explicitly requires it.
- Stop for user direction when a conflict or choice would change business behavior, API semantics, compatibility, state retention, or another user-owned decision.
- Respect repository-specific validation restrictions. Use static checks only when builds, compilers, or SDK queries are forbidden.

## Completion Reporting

- Report the operation performed, final branch, resulting commit when applicable, push status, validation performed, and any unresolved or user-owned follow-up.
- Distinguish a local commit from a pushed commit and a completed maintenance merge.
