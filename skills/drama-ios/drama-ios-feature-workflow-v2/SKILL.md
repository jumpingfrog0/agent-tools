---
name: drama-ios-feature-workflow-v2
description: Run the version 2 staged workflow for new drama-ios business features with explicit requirement confirmation, plan approval, incremental documents, executable tasks, UI-design cache integration, and evidence-backed delivery. Use when the user explicitly invokes $drama-ios-feature-workflow-v2, asks to start or continue the v2 iOS feature workflow, an active 执行.md declares workflow drama-ios-feature-workflow-v2, or v2 receives CONFIRM_REQUIREMENT, APPROVE_PLAN, REQUEST_CHANGES, or SKIP_BLOCKER. Do not use for ordinary bug fixes, code review, implementation discovery, or architecture discussion outside an active v2 workflow.
---

# drama-ios：iOS 新需求工作流 v2

以需求、方案、执行、交付四个阶段推进新业务需求。让 `执行.md` 成为唯一当前状态来源，使用最小补丁维护稳定事实，并让审批方案直接约束任务和实际 diff。

## 不可绕过的契约

- 未收到 `CONFIRM_REQUIREMENT` 前，不得形成可审批方案。
- 未收到 `APPROVE_PLAN` 前，不得修改生产代码、资源、工程文件或多语言产物。
- 需求变化必须重新确认；方案或审批范围变化必须重新审批。
- `执行.md` 是阶段、状态、阻塞、审批和任务进度的唯一来源；其他文档不得复制当前状态。
- 文件创建后不得整文件重新生成。只修改事实所属章节，内容未变化时不写文件。
- 任务完成前检查实际 diff、授权范围、方案约束和验证证据。
- 新增文案的多语言 key 未确认时保持阻塞，不修改多语言产物。

## 启动与恢复

1. 从需求名生成下划线风格 `<feature-id>`。
2. 新需求只从 `assets/需求.md` 和 `assets/执行.md` 创建对应文件；不要提前创建空方案或交付文档。
3. 已存在需求时先读取 `执行.md`。只有其 frontmatter 声明 `workflow: drama-ios-feature-workflow-v2` 才继续。
4. 根据 `stage` 和 `status` 读取当前阶段所需文档，不读取无关 feature 文档。
5. 完整读取 [references/工作流模型.md](references/工作流模型.md)，再按阶段加载对应 reference。

## 阶段路由

- `requirement` 或 `plan`：完整读取 [references/需求与方案.md](references/需求与方案.md)。
- `execution` 或 `delivery`：完整读取 [references/执行与交付.md](references/执行与交付.md)。
- 阶段回退时重新读取目标阶段 reference，不用会话记忆替代持久化事实。

## 增量更新

- 新结论先判断事实归属，只修改 `需求.md`、`方案.md`、`执行.md` 或 `交付.md` 中唯一对应位置。
- 澄清和评审期间维护“本轮待确认差量”或“本轮待审批差量”；无关章节保持字节不变。
- 确认或审批时固化差量、升级版本、追加一条精简事件，不重写正文。
- `REQUEST_CHANGES` 只更新受影响差量、任务和验收映射。
- `SKIP_BLOCKER` 只关闭对应阻塞；若改变需求或方案，再进入相应差量流程。

## UI 设计门禁

需求涉及 `design_images/` 时，在需求确认后的方案阶段调用 `$implement-ui-from-design-images`：

```text
caller_workflow=drama-ios-feature-workflow-v2
caller_stage=plan
execution_mode=implementation-read
precision_read_authorized=true
cache_policy=persist
force_refresh=false
approval_boundary=<当前需求和候选影响范围>
```

- 由 UI Skill 管理 `.ui-design-cache.md`；本工作流不得读取、维护或复制缓存正文。
- UI Skill 返回 fingerprint 和缓存状态供本轮判断；`方案.md` 只持久化 fingerprint、UI 职责、组件决策、资源方案、影响范围、视觉验证和门禁结论。缓存状态是瞬时诊断值，不写入方案。
- 缓存命中且审批级结论未变化时，不更新 `方案.md`。
- UI 发现用户可见行为变化时回到需求阶段；发现影响范围扩大时留在方案阶段重新审批。

## 固定口令

```text
CONFIRM_REQUIREMENT
APPROVE_PLAN
REQUEST_CHANGES: <变更内容>
SKIP_BLOCKER: <阻塞项和替代方案>
```

口令只在当前阶段和门禁允许时生效。拒绝无效推进，并明确剩余阻塞或缺失证据。
