# SkillHub

面向 AI 编程助手的 Skill 集合，收录通用研发工具与项目专用工作流。每个 Skill 以 `SKILL.md` 为入口，按需附带脚本、参考资料和文档模板。

## 目录结构

```text
skills/
├── common/       # 通用研发工具与跨项目工作流
├── drama-ios/    # drama-ios 项目专用能力
└── likee/        # Likee 项目专用工作流
```

## Skill 索引

### 通用工具

| Skill | 用途 |
| --- | --- |
| [discuss-design-decisions](skills/common/discuss-design-decisions/SKILL.md) | 对需要用户决策的高影响设计问题逐项讨论，明确关键取舍。 |
| [feature-discovery](skills/common/feature-discovery/SKILL.md) | 基于代码、配置、测试和运行证据，只读梳理已有功能的行为、实现链路与边界。 |
| [generate-weekly-report](skills/common/generate-weekly-report/SKILL.md) | 汇总多个本地 Git 仓库及相关 Codex 任务，按作者、时间范围去重整理工作周报。 |
| [git-workflow](skills/common/git-workflow/SKILL.md) | 按仓库约定提交代码，或执行功能分支到维护、发布分支的 rebase、合并与同步流程。 |
| [ios-to-android-feature-migration](skills/common/ios-to-android-feature-migration/SKILL.md) | 基于功能梳理文档，将已完成的 drama-ios 功能迁移到 famo-android；先编写迁移方案，确认后实现。 |
| [ipa-similarity-detection](skills/common/ipa-similarity-detection/SKILL.md) | 对比两个 iOS IPA 的二进制指纹与代码相似度，辅助评估包体复用及 App Store 4.3 风险。 |

### drama-ios

| Skill | 用途 |
| --- | --- |
| [drama-ios-feature-workflow](skills/drama-ios/drama-ios-feature-workflow/SKILL.md) | 显式启用的 iOS 新需求工作流，通过需求契约、技术方案及审批推进开发。 |
| [drama-ios-feature-workflow-v2](skills/drama-ios/drama-ios-feature-workflow-v2/SKILL.md) | 第二版分阶段需求工作流，包含需求确认、方案审批、增量文档、可执行任务与交付证据。 |
| [drama-ios-recharge-expert](skills/drama-ios/drama-ios-recharge-expert/SKILL.md) | 分析充值、钱包、IAP、支付结果与到账链路，收集证据、评估风险并明确修改范围。 |
| [drama-ios-refactor-architect](skills/drama-ios/drama-ios-refactor-architect/SKILL.md) | 为复杂 Objective-C 业务设计重构方案，梳理 UI、状态、异步流程及生命周期之间的职责。 |
| [drama-ios-remove-pbobjc-enums](skills/drama-ios/drama-ios-remove-pbobjc-enums/SKILL.md) | 根据当前 Git 变更，清理协议生成的 pbobjc 枚举辅助代码。 |
| [implement-ui-from-design-images](skills/drama-ios/implement-ui-from-design-images/SKILL.md) | 解析本地 UI 设计图，沉淀可复用设计信息，形成组件、资源、布局约束与视觉验证方案。 |

### Likee

| Skill | 用途 |
| --- | --- |
| [git-workflow-likee](skills/likee/git-workflow-likee/SKILL.md) | 执行 Likee 本地提交及功能分支 rebase 到最新 develop 的流程；rebase 完成后停止，不自动 merge 或 push。 |

## 使用方式

1. 从索引中选择符合任务与项目范围的 Skill，阅读其 `SKILL.md`，确认触发条件、依赖和执行边界。
2. 按所用助手的 Skill 加载方式配置对应目录。需要复制时，保留整个 Skill 文件夹，确保脚本、模板和相对路径引用完整。
3. 在支持按名称调用 Skill 的助手中，使用 `$<skill-name>` 显式调用，并提供任务所需的仓库路径、目标、输入材料和限制条件。

项目专用 Skill 可能依赖本地知识文件、工具或项目约定，具体以对应 `SKILL.md` 为准。位于 `common/` 的 Skill 也可能有明确的项目适用范围，使用前需检查说明。

## 维护约定

- 通用能力放在 `skills/common/`，项目专用能力放在 `skills/<project>/`。
- 每个 Skill 使用独立目录，在 `SKILL.md` 中说明名称、用途、触发条件与执行流程。
- 脚本、参考资料、模板及助手配置随 Skill 一起维护，按需放入 `scripts/`、`references/`、`assets/` 和 `agents/`。
- 新增、移动或调整 Skill 用途时，同步更新本页索引。
