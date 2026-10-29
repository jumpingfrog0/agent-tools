---
name: generate-weekly-report
description: Generate an evidence-based, reporting-oriented weekly work report from one or more caller-provided local Git repository directories and their related Codex tasks. Use when Codex needs to consolidate weekly activity across repositories, multiple working copies, or different checked-out branches; deduplicate commits and tasks; filter by authors and a time window; present cross-cutting technical initiatives and requirement-ID deliverables; produce an audit-style source summary; or power a scheduled weekly-report automation without embedding project-specific names or paths in the skill.
---

# Generate Weekly Report

Generate one concise report from runtime inputs. Treat every project name, directory, author, time range, timezone, grouping choice, and output preference as caller-provided data. Never embed or retain project-specific values in this skill.

## Inputs

Require:

- One or more absolute local Git repository directories.
- A bounded time range. Resolve relative wording into exact timestamps with timezone offsets before collecting Git data. Show it in audit mode or when the caller requests it; otherwise use it only as the evidence boundary.

Accept optional:

- Author names or email addresses. When omitted, include all authors and disclose that scope.
- Whether to include related Codex tasks; default to true when the required thread tools are available.
- A report title, product or release label, requirement IDs and names, and release context. Prefer caller-provided labels; extract them from evidence only when unambiguous.
- Presentation mode: `reporting` or `audit`. Default to `reporting`.
- Whether to include a separate cross-cutting technical initiative section.
- Grouping preferences, output language, headings, and additional caller rules.

Do not guess a missing directory or time range. Ask for it when running interactively; for unattended automation, return a short actionable error.

## Workflow

1. Validate every supplied directory. Continue with valid directories when one fails, and record skipped inputs in a warning section.
2. Run `scripts/collect_git_activity.py` with repeated `--repo` and optional repeated `--author` arguments plus exact `--since` and `--until` timestamps.
3. Use the script's `repository_id` to recognize working copies of the same repository. Deduplicate commits by `repository_id + commit SHA`.
4. If Codex task collection is enabled, list tasks across the local host, retain tasks associated with any supplied directory, and read only tasks that overlap the requested period. Deduplicate by host and task/thread ID.
5. Build canonical work items only from Git commits and task evidence. For each workstream, capture applicable requirement ID, requirement name, release context, concrete deliverables, implementation approach, technical value, and resolved or investigated problems. Leave unsupported fields empty.
6. Deduplicate the same fact across Git and Codex evidence. Allow one workstream to contribute to both a cross-cutting technical initiative and a requirement deliverable when they serve different reporting purposes: the technical item explains how and why, while the requirement item states what was completed. Do not repeat the same claim or wording in both places.
7. In reporting mode, group by caller preference, then cross-cutting technical initiative, requirement ID, business theme, and finally repository identity. Use repository grouping only when the evidence cannot be organized into meaningful reporting subjects.
8. In audit mode, group by normalized repository identity unless the caller requests another grouping. Use caller-provided labels when available; otherwise derive concise labels from repository metadata without writing them back into the skill.
9. Report incomplete sources explicitly when they could materially affect the result. Examples include inaccessible directories, missing remotes, unavailable task tools, unreadable tasks, and local refs that may be stale.

## Git collection

Run:

```bash
python3 <skill-dir>/scripts/collect_git_activity.py \
  --repo <absolute-directory> \
  --repo <absolute-directory> \
  --author <exact-name-or-email> \
  --since <ISO-8601-timestamp> \
  --until <ISO-8601-timestamp> \
  --pretty
```

Pass each runtime directory separately, including multiple working copies of the same repository. Author matching is case-insensitive and exact against the Git author name, email, or `Name <email>` form.

The collector reads `git log --all`, so it can include commits reachable from locally available refs without switching the checked-out branch. It does not contact remotes.

## Codex task collection

Use the Codex app's cross-host task listing and task-reading tools when available. Match tasks using canonical directory paths or project metadata, not only a display name. A task may belong to only one working copy even when several directories share a Git remote; include all supplied directories in the match set.

Use task summaries, user requests, decisions, and completed outcomes as evidence. Exclude speculative plans, abandoned approaches unless they explain delivered work, and unrelated tasks. Do not infer work merely from a task title.

If task tools are unavailable in an automation environment, complete the Git-based report and say that Codex task evidence was not available.

## Safety

Keep collection read-only:

- Do not run `git fetch`, `pull`, `checkout`, `switch`, `reset`, `clean`, `stash`, or commands that modify refs or working trees.
- Do not edit repository files or Codex task records.
- Do not silently broaden the time range or author filter.
- Do not count the same commit or task more than once.

## Output

Default to a concise, reporting-oriented weekly report.

### Reporting mode

Use this structure, omitting sections that lack evidence:

```markdown
# {report title}

1. **{cross-cutting technical initiative}**
   - {staged approach or implementation strategy}
   - {meaningful concrete scope}
   - {architectural, stability, delivery, maintenance, or debugging value}

2. **{requirement ID} {requirement name}**
   - {release background when supplied or unambiguously evidenced}
   - {localized concrete-work label}:
     - {completed feature, integration, or fix}
     - {completed feature, integration, or fix}

3. **{requirement ID or business theme}**
   - {completed outcome}
```

Apply these rules:

- Use a caller-provided report title. If absent, use a neutral title in the requested language; do not invent a product name or version.
- Put meaningful cross-requirement technical construction before individual requirement deliverables. Create this item only when evidence supports a distinct implementation approach and technical value, not merely because several files changed.
- Organize remaining top-level items by requirement ID or business theme. Do not use repository names as the default presentation structure.
- Keep each top-level item focused on one reporting subject and normally use two to five concise, outcome-oriented bullets.
- Explain technical initiatives at the reporting level: implementation stages, core design, affected scope, and resulting value. Avoid unnecessary class names, file names, raw commit details, and low-level debugging chronology.
- State concrete work under requirement items: completed features, integrations, UI behavior, stability fixes, and verified investigations. Include release context only when supplied or clearly evidenced.
- Integrate resolved or investigated problems into the related requirement or business theme instead of creating a generic investigation section.
- Do not show the reporting period, author list, commit count, repository statistics, evidence count, or source limitations in the main body unless the caller requests them.
- Add a compact warning section only when incomplete evidence could materially change the report.

### Audit mode

Produce a source-oriented report containing:

1. The exact reporting period, author scope, and evidence scope.
2. Completed work grouped according to the caller's preference or normalized repository identity.
3. Problems investigated or resolved when supported by evidence.
4. Commit and task counts when useful for verification.
5. A compact source-limitation or warning section only when needed.

In both modes, do not dump raw commit logs, fabricate intent or value, infer ambiguous release context, or add future plans unless the caller explicitly requests them and evidence supports them. Do not count the same commit or task more than once in evidence totals.
