# Delivery Report Template

Use this template after Android implementation.

## Android迁移实施记录.md

```markdown
# <功能名> Android迁移实施记录

- 作者：huangdonghong
- 迁移方案：<android-repo>/.huangdonghong/feature-migration/<feature-slug>/Android迁移方案.md
- 状态：已实施

## 1. 实际改动摘要

- <改动 1>
- <改动 2>

## 2. 文件改动

### Production Code

- `<path>`：<职责和改动>

### Resources and Strings

- `<path>`：<职责和改动>

### Documentation

- `<path>`：<职责和改动>

## 3. 与方案偏差

- 无偏差。

If there are deviations, list each deviation, reason, and impact.

## 4. 保留风险

- <risk or "无">
```

## Android迁移验收报告.md

```markdown
# <功能名> Android迁移验收报告

- 作者：huangdonghong
- 状态：已完成静态验证

## 1. 静态验证

| 检查项 | 命令/方式 | 结果 |
| --- | --- | --- |
| 代码搜索 | `rg ...` | 通过 |
| Diff 空白检查 | `git diff --check` | 通过 |

## 2. 未执行验证

Due to project constraints, explicitly list prohibited commands not run:

- 未运行 `./gradlew`
- 未运行 `gradle`
- 未运行 `adb`
- 未运行 `sdkmanager`
- 未运行 `emulator`

## 3. 手工验收场景

- <scenario 1>
- <scenario 2>

## 4. 残余风险与待确认

- <risk or "无">
```

## Final Response Requirements

After writing both records, the final response should include:

- What changed.
- What was intentionally not changed.
- Validation performed.
- Validation not run due to project constraints.
- Remaining user confirmation items, if any.
