---
name: drama-ios-refactor-architect
description: Use in drama-ios when designing complex iOS Objective-C business refactors, especially severe coupling between UIKit views, ViewModels, Managers, factories, models, protocols, controllers, lifecycle logic, async flows, or when the user asks how to split or redesign classes from a senior iOS business architecture perspective.
---

# drama-ios：复杂业务重构方案设计

作者：huangdonghong

## 核心定位

不要提交一个简单方案。先读真实代码，再以 10 年以上 iOS/Objective-C 业务开发经验判断：这个重构是否必要、业务边界在哪里、职责怎么拆、如何渐进迁移、风险和测试场景是什么。

本 skill 是方案设计 skill，不是原则清单，也不是默认执行代码改造。除非用户明确要求实现，否则优先做静态搜索、工程检查和可落地方案设计；遵循项目约定，不使用 `xcodebuild`。

## 适用场景

- 用户说两个或多个 iOS 类耦合严重，想知道“如何拆分 / 如何重构 / 如何设计更合理”。
- 用户明确要求资深 iOS 视角，不要泛泛原则。
- 复杂业务模块中 View / ViewModel / Manager / Factory / Model / Protocol / Controller 职责混杂。
- 现有复用让命名失真、业务入口混乱、生命周期不清、扩展困难、异常路径难维护。
- Objective-C、UIKit、Masonry、MVVM/ViewModel、异步回调、资源加载、动画展示、业务队列等场景均适用。

## 工作方式

1. **先读代码再判断**
   - 用 `rg` 搜目标类、调用点、协议、模型、工厂、ViewController 接入点、delegate、调试入口。
   - 至少确认：定义文件、主要调用方、数据来源、业务入口、生命周期入口、清理入口、开关逻辑、异常路径。
   - 不要只凭类名做抽象，不要把用户给的结论当成事实。

2. **识别真实耦合点**
   - 数据模型是否混合多种业务语义或 UI 状态。
   - View 是否同时承载多种展示形态、交互路径或动画生命周期。
   - ViewModel / Manager 是否同时负责数据转换、队列、请求、下载、播放、UI 创建、状态清理。
   - Factory 是否把不同业务输出成同一种弱语义对象，导致下游被迫判断类型。
   - 调用方是否为了复用而重复实例化同一个类，暴露命名和职责不准。
   - 协议、头文件或 category 是否放错层级，例如数据层依赖 UIKit 或渲染生命周期。

3. **先定业务边界**
   - 判断这些逻辑是否共享业务语义、展示容器、互斥关系、生命周期、开关规则或数据来源。
   - 清晰的业务入口不应为了“统一”而合并；只有生命周期和语义确实一致时才抽公共层。
   - 不为了抽象而引入新策略；优先保留现有行为、开关、埋点、兜底和异常处理。

4. **再定技术职责边界**
   - SRP：数据模型、业务编排、队列/状态机、渲染、资源加载、播放/动画、入口适配分层。
   - OCP：新增业务形态时优先新增 payload / adapter / renderer，而不是扩大一个大类的类型分支。
   - DIP：编排层依赖协议或抽象能力，不直接依赖具体 View 或具体资源实现。
   - 依赖方向清晰：数据模型不依赖 UI 层；渲染协议不塞进纯数据模型文件；Controller 不承担底层细节。
   - 命名体现业务职责，避免用旧业务名承载新业务语义。

5. **给出渐进迁移路径**
   - 先新增边界清晰的模型、协议、编排对象或渲染对象，再接入真实业务路径。
   - 保留旧类或旧 API 过渡，避免一次性大爆炸重写。
   - 再清理调试入口、旧实现、旧命名和无用分支。
   - 明确头文件、工程引用、调用点、旧路径兼容策略。

## 搜索清单

根据用户给的类名替换占位符，优先并行读取结果：

```bash
rg -n "<TargetClass>|<RelatedClass>|<RelatedViewModel>"
rg -n "<DelegateMethod>|<BusinessEntry>|<LifecycleMethod>|<ClearMethod>"
rg -n "<RelatedModel>|<RelatedItem>|<Payload>|<StateEnum>"
rg -n "<Factory>|<Builder>|<Adapter>|<Manager>|<Service>"
rg -n "@protocol .*<ProtocolName>|<ProtocolName>|<Renderable>|<DataSource>|<Delegate>"
rg -n "showType|type|scene|source|status|state|is[A-Z]|enable|switch|duration|completion"
```

必要时检查工程引用和头文件遗漏：

```bash
rg -n "<NewClass>|<OldClass>|<ProtocolName>" *.xcodeproj project.pbxproj
rg -n "#import \".*<ClassName>|@class <ClassName>|<ClassName> \\*" .
```

## 输出要求

输出要直接、务实、面向落地。推荐固定结构：

1. **结论**
   - 是否值得重构。
   - 核心业务边界是什么。
   - 哪些入口应该保留，哪些职责应该拆出。

2. **代码事实**
   - 用文件、类、方法、属性说明搜索到的事实。
   - 区分业务耦合、技术职责耦合、命名误导、生命周期风险。

3. **业务边界**
   - 说明哪些能力属于不同业务语义，哪些可以共享。
   - 说明为什么某些入口不应该合并，或者为什么某些流程可以共用。

4. **技术职责边界**
   - 明确新增、移动、保留、废弃的类 / 协议 / 模型 / 方法。
   - 明确依赖方向：谁依赖谁，哪些层不能互相依赖。
   - 说明为什么拆，以及为什么不做更重的抽象。

5. **迁移步骤**
   - 小步可验证，每步说明影响范围。
   - 包含头文件引入、工程引用、旧 API 兼容、旧代码清理时机。

6. **测试与风险**
   - 覆盖业务开关、生命周期、异常数据、异步回调、复用入口、旧路径兼容。
   - 覆盖 UI 布局、动画、RTL、资源失败、重复触发、退出页面清理等相关场景。
   - 指出需要用户自行编译验证的点；不要调用 `xcodebuild`。

## 判断标准

- **业务语义优先**：不要为了统一而合并清晰业务入口，也不要为了复用让命名失真。
- **职责单一**：一个对象不要同时承担数据转换、状态机、资源加载、UI 创建和生命周期清理。
- **依赖干净**：数据层不依赖 UIKit；渲染层协议放在渲染层附近；业务编排层依赖抽象能力。
- **渐进迁移**：先接入真实业务路径，再清理旧实现；每一步都能回滚和验证。
- **可读性优先**：命名必须让后续维护者看出业务职责，而不是只反映历史来源。
