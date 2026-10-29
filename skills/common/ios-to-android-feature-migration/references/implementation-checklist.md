# Implementation Checklist

Use this checklist only after the user confirms `Android迁移方案.md`.

## Coding Gate

Before editing Android code, confirm:

- `Android迁移方案.md` exists under `<android-repo>/.huangdonghong/feature-migration/<feature-slug>/`.
- The user explicitly confirmed the current `Android迁移方案.md`.
- The current `Android迁移方案.md` belongs to this migration target, not to a completed historical migration used only as background.
- The confirmed plan reflects the latest iOS feature-discovery documents.
- The plan status is not `待确认`, `待重新确认`, or `阻塞，待确认`.
- The plan has no blocking open questions.
- The plan has no unresolved alternatives in executable sections.
- The intended edits match the confirmed file/change scope.
- Android repository constraints have been read in the current task.

If any item is false, do not edit Android production code.

## Android Code Rules

- Keep changes scoped to the confirmed migration.
- Follow existing module ownership and dependency boundaries.
- Put cross-module interfaces under `src/header` and implementations under `src/main` when needed.
- Use Hilt, Athena `@ServiceRegister`, or `Axis.getService` for cross-module service access according to existing patterns.
- Do not introduce direct business-module coupling.
- Use existing network, RPC, serialization, image, video, list, paging, and storage helpers.
- Use `ALog` for logs and define `TAG` in `companion object`.
- Use `KvPreference` and `SpData.withUid()` conventions for storage when applicable.
- Do not hardcode user-facing strings; use existing multilingual/efox/configuration flow.
- Reuse `base-res` and target-module resources before adding new ones.

## Android UI Rules

- Continue the target page's existing UI technology: ViewBinding or Compose.
- Use `clickWithTrigger` for click handling.
- Use `start/end` constraints for new XML constraints.
- Avoid raw px; use existing dimension utilities or dimens resources.
- Use project shape/selector DSL for dynamic backgrounds.
- Prefer existing font/typeface components for bold text.

## Validation Rules

Run only validation allowed by the project constraints, typically:

- Static search with `rg`.
- Text inspection.
- `git diff --check`.

Do not proactively run:

- `./gradlew`
- `gradle`
- `adb`
- `sdkmanager`
- `emulator`

## Delivery Record Inputs

Track during implementation:

- Files actually changed.
- Differences from the confirmed plan.
- Validation commands run and results.
- Commands intentionally not run due to project rules.
- Remaining risks or manual verification needs.
