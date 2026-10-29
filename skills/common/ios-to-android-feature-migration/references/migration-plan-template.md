# Android Migration Plan Template

Use this template for:

```text
<android-repo>/.huangdonghong/feature-migration/<feature-slug>/Android迁移方案.md
```

The plan must be written before Android code changes and must be confirmed by the user before implementation.

The input feature-discovery documents must come from the iOS repository, not from the Android repository:

```text
<ios-repo>/.huangdonghong/docs/<feature-slug>/<feature-name>业务梳理.md
<ios-repo>/.huangdonghong/docs/<feature-slug>/<feature-name>技术实现梳理.md
```

## Header

```markdown
# <功能名> Android迁移方案

- 作者：huangdonghong
- Android仓库：famo-android
- iOS仓库：drama-ios
- 输入业务文档：<ios-repo>/.huangdonghong/docs/<feature-slug>/<feature-name>业务梳理.md
- 输入技术文档：<ios-repo>/.huangdonghong/docs/<feature-slug>/<feature-name>技术实现梳理.md
- 关联历史迁移基准：<无 / <android-repo>/.huangdonghong/feature-migration/<historical-feature-slug>/Android迁移方案.md>
- 输出目录：<android-repo>/.huangdonghong/feature-migration/<feature-slug>/
- 状态：待确认
```

`关联历史迁移基准` is optional and only records read-only background from a completed related migration. It is not the approval baseline for the current migration and must not be modified by the current plan.

Allowed status values:

- `待确认`: first version of the plan is waiting for user review.
- `待重新确认`: the plan was refreshed after upstream iOS documents changed and must be reviewed again.
- `阻塞，待确认`: blocking questions remain and implementation is not allowed.
- `已确认`: the user explicitly confirmed the current plan version.

## Required Sections

### 1. 迁移目标

- State the exact Android user-facing behavior to deliver.
- State the iOS feature scope being migrated.
- State any explicitly excluded behavior.

### 2. iOS事实摘要

Summarize only facts supported by feature-discovery documents or targeted code evidence:

- User path and entry points.
- Business rules and state transitions.
- API/RPC/model fields.
- Configuration, experiment, feature flag, and server switch dependencies.
- Resource, string, and analytics dependencies.
- Empty, loading, error, disabled, fallback, and compatibility behavior.

### 3. iOS证据抽查结论

- List inspected iOS files/classes/functions.
- Record confirmed facts.
- Record conflicts between documents and code.
- Record missing evidence.
- Mark conflicts that block implementation decisions.

### 4. Android现状与差异

- Existing Android entry points and nearest feature patterns.
- Existing modules and ownership boundaries.
- Existing protocol/API/resource/storage/analytics capabilities.
- Behavior gaps between iOS and Android.
- Android-specific compatibility or product differences.

### 5. Android实现方案

Provide one decision-complete implementation path:

- Target module and package.
- Classes, layouts, resources, protocol interfaces, and data models to add or modify.
- Data flow and state flow.
- Network/RPC integration.
- Local storage and cache rules.
- UI implementation approach and lifecycle handling.
- Resource, string, and efox/configuration handling.
- Analytics/logging changes.
- Error, empty, loading, disabled, fallback, and edge states.

Decision completeness check:

- Keep only the current chosen path in executable content.
- Do not use unresolved alternatives such as `A 或 B`, `A/B`, `可选`, `也可以`, `方案一/方案二`, or `实现时决定`.
- If alternatives were considered, mention only discarded alternatives briefly and keep them out of the execution path.
- If one path cannot be chosen from evidence, move the unresolved decision to `风险与待确认问题` and set status to `阻塞，待确认`.

### 6. 文件改动清单

List expected Android files grouped by purpose:

- Production code.
- Resources and strings.
- Protocol/header interfaces.
- Documentation.

Keep this scoped to the confirmed migration only.

### 7. 验证计划

List only validation allowed by the Android project constraints:

- Static searches.
- Text checks.
- `git diff --check`.
- Manual acceptance scenarios.

Explicitly state prohibited commands that will not be run, such as Gradle, adb, sdkmanager, or emulator commands, when the project rules prohibit them.

### 8. 风险与待确认问题

- Blocking questions that must be resolved before coding.
- Non-blocking risks.
- Missing evidence.
- Product or backend dependencies.

If any blocking question remains, set plan status to "阻塞，待确认" and do not implement.

## Requirement Supplement Section

When the plan is refreshed after upstream iOS feature-discovery documents were supplemented or corrected, add or update:

```markdown
### 需求补充影响评估

- 补充来源业务文档：<ios-repo>/.huangdonghong/docs/<feature-slug>/<feature-name>业务梳理.md
- 补充来源技术文档：<ios-repo>/.huangdonghong/docs/<feature-slug>/<feature-name>技术实现梳理.md
- 本次刷新时间：<YYYY-MM-DD HH:mm>
- 新增/变化需求点：
  - <requirement change>
- Android影响范围：
  - <affected Android scope or "无实现影响">
- 方案更新结论：
  - <sections/files/risks/validation updated>
- 阻塞问题：<无 or blocking question>
```

If the supplement does not change Android implementation, still keep this section and set the plan status to `待重新确认`.
