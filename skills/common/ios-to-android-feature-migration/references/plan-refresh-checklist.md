# Plan Refresh Checklist

Use this checklist when an existing `Android迁移方案.md` must be refreshed because upstream iOS feature-discovery documents were supplemented, corrected, or found incomplete after the plan was written, and the migration has not completed implementation and delivery records.

Do not use this checklist when `Android迁移实施记录.md` and `Android迁移验收报告.md` both exist for the same migration directory. In that case, the existing `Android迁移方案.md` is a historical migration baseline and remains read-only. Later-added capability must be handled as a new migration target with a new `<feature-slug>`.

## Gate

- Update the existing `<android-repo>/.huangdonghong/feature-migration/<feature-slug>/Android迁移方案.md`.
- This gate applies only to an unfinished migration. If implementation and acceptance records both exist, stop and switch to a new migration target.
- After refresh, set the plan status to `待重新确认`, or `阻塞，待确认` if a blocking issue remains.
- Do not carry over an earlier confirmation automatically. The refreshed plan requires explicit user confirmation again.

## Inputs

Read all of these before editing the plan:

- Latest iOS business document: `<ios-repo>/.huangdonghong/docs/<feature-slug>/<feature-name>业务梳理.md`
- Latest iOS technical document: `<ios-repo>/.huangdonghong/docs/<feature-slug>/<feature-name>技术实现梳理.md`
- Existing Android migration plan: `<android-repo>/.huangdonghong/feature-migration/<feature-slug>/Android迁移方案.md`

The iOS documents remain the source of business and technical facts. The existing Android plan is stale until refreshed.

## Change Classification

Compare the latest iOS documents with the existing Android plan and classify every relevant change:

- Added requirement: new behavior, state, UI, API, config, analytics, resource, or edge case.
- Modified requirement: existing behavior changed or gained conditions.
- Removed requirement: behavior in the old plan is no longer supported by current iOS documents.
- Conflict: latest documents contradict the old plan or checked iOS code evidence.
- No Android impact: documented supplement does not change Android implementation, validation, risk, or file scope.

## Impact Analysis

For each added, modified, removed, or conflicting item, update the plan impact:

- iOS facts summary.
- iOS evidence checking result.
- Android current-state and gap analysis.
- Android implementation approach.
- File change list.
- Validation plan.
- Risks and pending questions.

If a change affects implementation decisions and evidence is insufficient, mark it as blocking and set status to `阻塞，待确认`.

## Required Plan Update

Add or update a section named:

```markdown
### 需求补充影响评估
```

The section must include:

- Supplement source document paths.
- Refresh time or current date/time when known.
- Added, modified, removed, conflicting, and no-impact items.
- Android impact for each item.
- Sections updated in the migration plan.
- Whether blocking questions remain.

If no Android code change is required, record `无实现影响` and still set status to `待重新确认`.

## Quality Check

Before reporting completion, apply `Plan Quality Gate` from `SKILL.md`:

- Check executable sections for unresolved alternatives.
- Choose one path when evidence decides it.
- Move undecidable alternatives to `风险与待确认问题` and set status to `阻塞，待确认`.

## Final Response

After refreshing the plan:

- Report the updated plan path.
- Summarize the requirement supplement impact.
- State that Android production code was not modified.
- State that implementation remains blocked until the refreshed plan is explicitly confirmed.
