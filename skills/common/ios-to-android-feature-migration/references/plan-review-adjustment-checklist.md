# Plan Review Adjustment Checklist

Use this checklist when user review feedback requires directly correcting the Android technical migration plan before implementation.

## Gate

- Update the existing `<android-repo>/.huangdonghong/feature-migration/<feature-slug>/Android迁移方案.md`.
- Keep the plan as the current clean implementation plan.
- Do not add a review adjustment history section.
- Do not record the old plan, adjustment reasons, or audit-style impact history.
- After adjustment, set the plan status to `待确认`, or `阻塞，待确认` if a blocking issue remains.

## Inputs

Read before editing the plan:

- Existing Android migration plan: `<android-repo>/.huangdonghong/feature-migration/<feature-slug>/Android迁移方案.md`
- User review feedback.

If the review feedback questions an iOS fact, read the final iOS feature-discovery documents only as fact constraints:

- `<ios-repo>/.huangdonghong/docs/<feature-slug>/<feature-name>业务梳理.md`
- `<ios-repo>/.huangdonghong/docs/<feature-slug>/<feature-name>技术实现梳理.md`

Do not redo feature discovery.

## Adjustment Rules

- Identify which existing plan sections the review feedback affects.
- Directly rewrite affected sections so the plan remains a single current version.
- Keep unrelated sections unchanged unless they conflict with the adjusted technical plan.
- Synchronize all dependent sections:
  - Android implementation plan.
  - File change list.
  - Validation plan.
  - Risks and pending questions.
- If the adjustment introduces an unresolved decision, set status to `阻塞，待确认`.
- If no blocking issue remains, set status to `待确认`.

## Quality Check

Before reporting completion, apply `Plan Quality Gate` from `SKILL.md`:

- Check executable sections for unresolved alternatives.
- Choose one path when evidence decides it.
- Move undecidable alternatives to `风险与待确认问题` and set status to `阻塞，待确认`.

## Final Response

After adjusting the plan:

- Report the updated plan path.
- Briefly summarize the current technical plan result.
- State that Android production code was not modified.
- State that implementation remains blocked until the current plan is explicitly confirmed.
