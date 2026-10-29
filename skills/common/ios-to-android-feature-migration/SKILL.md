---
name: ios-to-android-feature-migration
description: Use when migrating a completed iOS feature from drama-ios to famo-android, based on feature-discovery final business and technical documents. Also use when upstream iOS feature-discovery documents were supplemented, corrected, or found incomplete after an Android migration plan was written, or when user review feedback requires directly correcting the Android technical migration plan before implementation. Requires writing or updating the Android migration plan first and waiting for user confirmation before modifying Android code.
---

# iOS to Android Feature Migration

Use this skill to migrate an already completed iOS feature from `drama-ios` to `famo-android`. This skill consumes the final documents produced by `feature-discovery`; it does not replace feature discovery.

## Scope

This skill owns:

- Consuming final iOS `feature-discovery` documents.
- Validating migration-critical iOS facts with targeted code checks.
- Writing, refreshing, or correcting `Android迁移方案.md`.
- Implementing Android only after the current plan is explicitly confirmed.
- Producing implementation and acceptance records.

This skill does not own:

- Full iOS feature exploration.
- Replacing or shortcutting `feature-discovery`.
- Modifying Android code before a written migration plan is confirmed.
- Running Android build, install, SDK, emulator, or adb commands when the Android project constraints prohibit them.

## Required Inputs

Before starting a real migration, locate the iOS repository first, then read both final feature-discovery documents from the iOS repository:

```text
<ios-repo>/.huangdonghong/docs/<feature-slug>/<feature-name>业务梳理.md
<ios-repo>/.huangdonghong/docs/<feature-slug>/<feature-name>技术实现梳理.md
```

Default `<ios-repo>` is `../drama-ios` relative to the Android repository `famo-android`. Do not search the Android repository `.huangdonghong/docs` as the required iOS feature-discovery input location.

If either document is missing, stop the migration workflow and instruct the user to run `feature-discovery` for the iOS feature first. Do not infer the migration plan directly from iOS code when the final documents are absent.

The feature-discovery documents are the primary source of truth. iOS code inspection is mandatory only as targeted evidence checking for migration-critical facts, not as a full rediscovery pass.

## Repository Rules

Before writing a migration plan or editing Android code:

- Read and follow the current Android repository constraints, including `AGENTS.md`.
- Locate the iOS repository at `../drama-ios` relative to `famo-android`. If that path does not exist, stop and ask the user for the iOS repository path.
- If the iOS repository has its own local instructions, read and follow them for iOS evidence inspection.
- Keep Android changes limited to files directly required by the confirmed migration plan.

## Output Directory

For a real migration, write all Android migration artifacts under the Android repository:

```text
<android-repo>/.huangdonghong/feature-migration/<feature-slug>/
```

Default `<android-repo>` is the current `famo-android` repository. The iOS feature-discovery input documents stay in `<ios-repo>/.huangdonghong/docs`; the Android migration plan and delivery records stay in `<android-repo>/.huangdonghong/feature-migration`.

The required artifact files are:

```text
Android迁移方案.md
Android迁移实施记录.md
Android迁移验收报告.md
```

`Android迁移方案.md` is a required coding gate. If it has not been written, Android production code must not be modified.

## Migration Type Decision

Before choosing a workflow, classify the request:

- `首次迁移`: the current migration target has no corresponding `Android迁移方案.md`; use `First-Time Migration Workflow`.
- `方案刷新`: the current migration has not completed implementation and delivery records, and the user says the existing plan must be revised from updated iOS inputs; use `Plan Refresh Workflow`.
- `评审调整`: the current migration has not completed implementation and delivery records, and the user asks to adjust the existing technical migration plan before implementation; use `Plan Review Adjustment Workflow`.
- `新的迁移需求`: related migration artifacts exist, but the user is asking for later-added capability or a new target after the related migration already completed; generate a new `<feature-slug>` and use `First-Time Migration Workflow`.

## Completed Migration Protection

If a migration directory contains both `Android迁移实施记录.md` and `Android迁移验收报告.md`, treat its `Android迁移方案.md` as a historical migration baseline.

Historical migration baselines are read-only. 历史迁移基准只读，不得改为 `待重新确认`，不得按后续事实反向改写。Do not refresh them from later facts, and do not rewrite them to match later implementation or newer upstream documents.

Conclusions in a historical baseline represent only that migration's scope and facts at the time. They are not blockers for a later `新的迁移需求`.

For `新的迁移需求`, create a new `<feature-slug>` and write the standard artifact set under:

```text
<android-repo>/.huangdonghong/feature-migration/<new-feature-slug>/
```

Do not create an `increments/` directory and do not create `Android增量迁移方案.md`.

## First-Time Migration Workflow

1. Read Android repository constraints and relevant project documentation.
2. Locate the iOS repository and read its applicable local constraints.
3. Locate and read the two final feature-discovery documents from `<ios-repo>/.huangdonghong/docs`.
4. Read `references/ios-evidence-checklist.md`, then inspect only the iOS evidence needed to validate migration-critical facts.
5. Read `references/android-analysis-checklist.md`, then inspect Android code to identify the correct module, entry points, interfaces, resources, data flow, storage, analytics, and existing patterns.
6. Read `references/migration-plan-template.md`, then write `<android-repo>/.huangdonghong/feature-migration/<feature-slug>/Android迁移方案.md`.
7. Apply `Plan Quality Gate`, report the plan path, and wait for explicit user confirmation.
8. After confirmation, read `references/implementation-checklist.md`, implement within the confirmed scope, run allowed validation only, then write delivery records from `references/delivery-report-template.md`.

## Plan Refresh Workflow

Use this workflow only when `Android迁移方案.md` already exists, implementation has not completed, delivery records are not both present, and the user says the iOS feature-discovery documents were supplemented, corrected, found incomplete, or updated after plan review.

If implementation and delivery records are both present, do not use this workflow. Treat the existing plan as a historical migration baseline and classify later-added capability as `新的迁移需求`.

1. Do not modify Android production code.
2. Read the latest feature-discovery documents from `<ios-repo>/.huangdonghong/docs`.
3. Read the existing `<android-repo>/.huangdonghong/feature-migration/<feature-slug>/Android迁移方案.md`.
4. Read `references/plan-refresh-checklist.md`.
5. Compare the latest iOS documents with the existing Android migration plan.
6. Update the same `Android迁移方案.md`, including `需求补充影响评估` and every affected execution section.
7. Set plan status to `待重新确认`, or `阻塞，待确认` if a blocking issue remains.
8. Apply `Plan Quality Gate`, then stop and wait for explicit user confirmation.

## Plan Review Adjustment Workflow

Use this workflow when `Android迁移方案.md` already exists, implementation has not completed, delivery records are not both present, and the user says the Android technical plan, module choice, implementation path, file list, validation plan, or risk judgment is unreasonable and must be adjusted before implementation. Use `Plan Refresh Workflow` instead when the change comes from updated iOS feature-discovery documents.

If implementation and delivery records are both present, do not use this workflow. Treat the existing plan as a historical migration baseline and classify later-added capability as `新的迁移需求`.

1. Do not modify Android production code.
2. Read the existing `<android-repo>/.huangdonghong/feature-migration/<feature-slug>/Android迁移方案.md`.
3. Read `references/plan-review-adjustment-checklist.md`.
4. Apply the user review feedback by directly rewriting the affected plan sections.
5. Keep the plan as one clean, current implementation plan; do not record old wording, adjustment reasons, or review history.
6. Set plan status to `待确认`, or `阻塞，待确认` if a blocking issue remains.
7. Apply `Plan Quality Gate`, then stop and wait for explicit user confirmation.

## Plan Quality Gate

Apply this gate after writing or updating `Android迁移方案.md` and before reporting completion:

- Executable sections must contain one chosen implementation path. This includes `Android实现方案`, `文件改动清单`, `验证计划`, and `风险与待确认问题`.
- Do not leave unresolved alternatives as execution conclusions, including `A 或 B`, `A/B`, `可选`, `也可以`, `方案一/方案二`, or `实现时决定`.
- If code evidence, project rules, or existing patterns decide the issue, choose one path and update all affected sections.
- If the issue cannot be decided from evidence, move it to `风险与待确认问题`, set status to `阻塞，待确认`, and stop.
- If unresolved alternatives remain in executable sections, the plan is not ready for confirmation or implementation.

## Hard Gates

- Missing final business document: stop and request `feature-discovery`.
- Missing final technical document: stop and request `feature-discovery`.
- Missing Android migration plan file: do not edit Android production code.
- No explicit user confirmation of the migration plan: do not edit Android production code.
- Blocking open questions in the migration plan: do not edit Android production code until resolved.
- Conflict between feature-discovery documents and checked iOS code: record the conflict in the migration plan and stop if it affects implementation decisions.
- Upstream iOS feature-discovery documents changed before implementation completed: treat the existing plan as stale, refresh the same plan file, and wait for user confirmation again before editing Android code.
- Upstream iOS feature-discovery documents changed after implementation and delivery records completed: keep the existing plan read-only as a historical migration baseline and start a `新的迁移需求` with a new `<feature-slug>`.
- Existing plan status is `待确认`, `待重新确认`, or `阻塞，待确认`: do not edit Android production code.
- Unresolved alternatives remain in executable plan sections: choose one path or mark the plan as `阻塞，待确认`; do not treat the plan as ready.

## Evidence Rules

Use this source priority:

1. Final feature-discovery documents.
2. Targeted iOS code evidence.
3. Existing Android implementation patterns.
4. User-provided clarification.

Do not present guesses as confirmed facts. When evidence is missing, write it as missing evidence or a pending question. Configuration, experiments, feature flags, resources, strings, analytics, persistence, and fallback behavior must be explicitly checked or explicitly marked as not found.

## Reference Loading

Load references only when their workflow step is reached:

- `references/ios-evidence-checklist.md`: before targeted iOS evidence inspection.
- `references/android-analysis-checklist.md`: before Android implementation analysis.
- `references/migration-plan-template.md`: before writing `Android迁移方案.md`.
- `references/plan-refresh-checklist.md`: when an existing Android migration plan must be refreshed after upstream iOS feature-discovery documents were supplemented or corrected.
- `references/plan-review-adjustment-checklist.md`: when user review feedback requires directly correcting the Android technical migration plan before implementation.
- `references/implementation-checklist.md`: after plan confirmation and before code edits.
- `references/delivery-report-template.md`: after implementation and before writing delivery records.
