---
name: implement-ui-from-design-images
description: Analyze local UI design images, persist reusable design facts, and translate them into an implementation-ready UI structure, component reuse decisions, asset plan, constraints, and visual validation plan. Use standalone or from another development workflow when UI references are stored in design_images, icons are supplied under design_images/icons, or precise design-image reading is required before UI implementation. When a formal staged workflow is active, require explicit caller stage, precision-read authorization, approval boundary, and cache policy before inspecting images, code, or cache files.
---

# 从设计图实施 UI

精读本地设计图片，缓存可恢复的设计事实，并结合当前需求和代码形成 UI 落地结论。既可独立使用，也可作为其他开发工作流的条件门禁。

## 调用边界

- 独立调用时，根据用户请求完成设计精读；只有用户同时授权实施时才修改生产代码。
- 被其他工作流调用时，服从调用方提供的阶段、审批边界和文档规则，不自行推进外部工作流。
- 正式分阶段工作流处于活动状态时，不得把目录出现、材料补充或本 Skill 自动触发解释为精读授权。
- 只确认设计事实和 UI 落地方案，不确认业务需求，不改变用户可见规则，不决定外部审批状态。
- 缓存只保存设计事实；组件复用、代码映射和影响范围必须结合每次调用的当前代码重新评估。
- 遵循目标仓库的 `AGENTS.md`、平台规范和验证限制。

## 执行模式与阶段保护

支持：

- `standalone`：用户独立要求精读；默认 `cache_policy=off`。
- `implementation-read`：由正式工作流调用；必须显式提供缓存策略。

正式工作流调用时，在枚举图片、运行 fingerprint 脚本、读取或写入缓存、搜索代码前检查：

1. `caller_workflow` 已明确。
2. `caller_stage` 已明确。
3. `execution_mode=implementation-read`。
4. `precision_read_authorized=true`。
5. `approval_boundary` 已提供并允许当前阶段精读。
6. `cache_policy` 已明确。

任一项缺失或冲突时立即停止，不读取图片、缓存或代码，也不形成 UI 决策。

## 输入契约

确定以下输入；正式工作流调用时不得从目录或模糊措辞推断前六项：

1. `caller_workflow`，独立调用填写 `standalone`。
2. `caller_stage`，独立调用填写 `standalone`。
3. `execution_mode=standalone | implementation-read`。
4. `precision_read_authorized=true | false`。
5. `approval_boundary`。
6. `cache_policy=off | persist`。
7. `force_refresh=false | true`，默认 `false`。
8. 任务根目录或明确的 `design_images` 路径。
9. 已确认的视觉、交互和内容约束。
10. 目标平台、当前实现范围及候选复用组件范围。
11. 图片倍率声明；未声明时使用默认倍率。
12. 允许执行的验证方式。

调用方不再维护或传入已有 fingerprint；本 Skill 自行计算并管理缓存。

## 目录、倍率与缓存位置

按以下顺序解析设计目录：

1. 使用明确给出的 `design_images` 路径。
2. 已给出任务根目录时，使用 `<task-root>/design_images/`。
3. 独立调用且未给出路径时，使用当前任务目录下的 `design_images/`。
4. 目录不存在时报告材料缺失，不做仓库级模糊搜索。

目录语义：

```text
design_images/
  <页面、弹窗或状态设计图>
  icons/
    <新增图标或图片资源>
```

- 根目录图片是页面、弹窗或状态设计图；`icons/` 中的文件是独立原始资源。
- 不得从页面截图重新裁切 `icons/` 已提供的资源。
- 默认倍率为 `1x`；只有明确声明时才覆盖。
- 默认按 `1 px = 1 设计布局单位` 解释；其他倍率按像素尺寸除以倍率换算。
- 不得根据文件名、画布大小或观感猜测倍率。
- `scale_spec` 使用 `default=<倍率>`；混用倍率时追加按相对路径升序排列的 `<路径或目录>=<倍率>`，以分号连接，例如 `default=1x;icons=2x`。不得根据文件名、画布大小或观感猜测倍率。

缓存固定为任务根目录下的 `.ui-design-cache.md`。仅提供设计目录时，任务根目录取该目录的父目录。不得让调用方指定其他缓存位置。

## Fingerprint 与缓存

使用 `scripts/design_fingerprint.py` 计算 fingerprint：

```bash
python3 <skill-dir>/scripts/design_fingerprint.py <design_images-path>
```

缓存命中必须同时满足：

- `force_refresh=false`。
- 当前 fingerprint 与缓存一致。
- 当前 `scale_spec` 与缓存一致。
- 缓存 `schema_version=1` 且必需章节可读取。

缓存状态：

- `disabled`：`cache_policy=off`。
- `hit`：缓存有效，直接复用设计事实。
- `miss`：`cache_policy=persist`，调用开始时没有缓存；完成精读后创建缓存。
- `refreshed`：`cache_policy=persist`，已有缓存失效或 `force_refresh=true`；完成精读后更新缓存。

命中缓存时禁止打开图片、运行 Pillow 或重新测量；加载缓存设计事实后，继续执行当前代码映射、组件判断、资源接入和门禁检查。

未命中时完整精读。`cache_policy=persist` 时将当前设计事实写入缓存；写入失败视为阻塞，不得伪装为可复用结论。`cache_policy=off` 时不读取、不创建也不更新缓存。

## 缓存契约

缓存 frontmatter：

```yaml
---
schema_version: 1
design_fingerprint: <sha256>
scale_spec: <规范化倍率声明>
---
```

正文只保存可恢复的设计事实：

- 输入文件、倍率、尺寸、颜色模式和 Alpha。
- 页面层级、布局分区和内容优先级。
- 所有会影响实施的尺寸、间距和显示约束。
- 默认、选中、禁用、加载、失败等状态。
- 点击、滚动、收展、弹出和关闭关系。
- 图标、图片、透明边距和显示方式等资源事实。

正文使用固定章节，缺少任一章节即视为 schema 无效：

```markdown
## 输入清单
<!-- 相对路径、倍率、像素尺寸、颜色模式、Alpha -->

## 页面结构与布局

## 尺寸与间距

## 状态与交互

## 资源事实
```

不得保存：

- Pillow 命令和测量流水账。
- 临时推理、搜索结果和被否决方案长篇比较。
- 客户端类、文件、组件映射和调用方影响范围。
- 外部工作流阶段、审批、任务或 checkpoint。

缓存只保存当前有效事实，不维护历史版本。更新时只替换受输入变化影响的事实，不追加历史分析流水账。

## 精读与映射流程

1. 计算 fingerprint 并判断缓存状态。
2. 缓存命中时加载设计事实；否则检查材料并执行原始像素读取。
3. 梳理页面层级、布局分区、状态和交互语义。
4. 按缓存策略写入当前设计事实。
5. 静态阅读当前目标代码，重新评估 UI 结构和组件边界。
6. 形成资源方案、视觉验证计划和门禁结论。

### 原始像素读取

- 使用 Pillow 读取尺寸、mode、Alpha、有效像素边界及必要颜色或坐标。
- 逐张以原始清晰度检查，不以缩略图或压缩预览代替。
- 详细测量过程不写入缓存；只写最终会影响实施的设计事实。
- Figma 等平台输入由对应专用 Skill 读取，本 Skill 继续负责缓存和落地判断。

### UI 结构与组件判断

- 按单一职责划分容器、区块和可复用单元。
- 与设计一致时直接复用。
- 差异有限且共享影响可控时，检查全部调用方后最小修改。
- 修改会影响其他功能时，保留共享组件并使用任务范围内的专用组件。
- 原有划分不合理时，在授权范围内重新拆分或合并。

### 资源方案

- 优先使用 `design_images/icons/` 中的原始资源。
- 明确每项资源是复用、迁移、新增还是无需接入。
- 资源缺失、版本冲突、用途不明或需要猜测时保持阻塞。
- 平台目录、命名、工程引用和 target 接入遵循目标仓库规则。

## 门禁

全部满足时才可通过：

- 材料和缓存状态可用，倍率明确，页面与状态足以实施。
- UI 层级、交互区域和关键状态已确认。
- 组件复用、专用组件和职责拆分已收敛。
- 资源来源和处理方式明确。
- 未发现与已确认用户可见规则冲突的设计内容。
- 实施范围和视觉验证计划明确。

设计改变用户可见行为时返回需求确认；实现超出调用方边界时返回计划审批。内部 UI 组织调整只有在授权范围内才可继续。

## 输出契约

返回：

1. 调用元数据和授权检查结果。
2. 设计目录、材料完整性和倍率。
3. fingerprint、`scale_spec`、缓存状态及是否执行图片精读。
4. 页面、状态和图标清单。
5. UI 结构与职责划分。
6. 组件复用、最小修改或专用组件决策。
7. 资源处理和平台接入要求。
8. 阻塞项及解除条件。
9. 用户可见行为影响。
10. 审批范围影响。
11. 视觉验证计划。
12. 门禁结论：通过、阻塞、退回需求确认或退回计划审批。

不输出缓存全文和测量流水账。被工作流调用时只返回结论，由调用方决定阶段和审批；独立调用且用户已授权实施时，门禁通过后再编码。
