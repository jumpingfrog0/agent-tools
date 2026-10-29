---
name: drama-ios-remove-pbobjc-enums
description: Use when working in drama-ios to remove generated pbobjc enum helper code based on current git status, especially after proto regeneration, pre_ci_build.sh enum cleanup, remove_pbobjc_enums.py, or phrases like 删除 pb 枚举值、清理 pbobjc 枚举辅助代码、移除协议枚举值.
---

# drama-ios：基于 git status 清理 pbobjc 枚举辅助代码

## Overview

`pre_ci_build.sh` 在混淆链路里会调用 `confuse/remove_pbobjc_enums.py`，用于把新版 `protoc` 生成出来的枚举辅助代码清掉，例如：

- `*_EnumDescriptor(void)`
- `*_IsValidValue(int32_t value)`
- `*_RawValue(...)`
- `GPBFieldHasEnumDescriptor`
- `GPBDataTypeEnum`
- `GPBFileDescription.package`

这个 skill 的目标不是全目录扫描，而是**仅处理当前 `git status` 里已变更的 `*.pbobjc.h/.m`**，避免误伤整个 `Cores/pbobjc` 或 `DramaApp/Protos/pbobjc`。

## When to Use

- 刚重新生成了 pbobjc，`git status` 里出现大量枚举描述函数和 `RawValue` 辅助方法。
- 需要把 `pre_ci_build.sh` 里的“删除协议枚举值”动作提前本地执行。
- 需要只针对当前变更集处理，而不是扫描整个 pbobjc 目录。

## Main Flow

在仓库根目录执行：

```bash
# 仅预览当前会处理哪些 pbobjc 文件
python3 .agents/skills/drama-ios-remove-pbobjc-enums/scripts/remove_pbobjc_enums_from_git_status.py

# 真正写盘
python3 .agents/skills/drama-ios-remove-pbobjc-enums/scripts/remove_pbobjc_enums_from_git_status.py --apply
```

可选参数：

- `--files PATH [PATH ...]`：不读 `git status`，只处理指定 pbobjc 文件。
- `--root PATH`：显式指定仓库根目录，默认自动推导。

## Verification

执行后建议复核：

```bash
git diff -- Cores/pbobjc DramaApp/Protos/pbobjc
rg '_EnumDescriptor|_IsValidValue|_RawValue|GPBFieldHasEnumDescriptor|GPBDataTypeEnum|\\.package = "[^"]+"' Cores/pbobjc DramaApp/Protos/pbobjc
```

## Notes

- 这个 skill 只自动改 `pbobjc.h/.m`，**不会**联动修改 `FamSvc*Types`、`IFamSvc*Core`、`FamSvc*Core.m` 之类包装层。
- 如果当前 feature 同时带来了新 RPC、新字段或新 wrapper，包装层要继续按业务需要手动核对。
- 默认是 `dry-run`；只有加 `--apply` 才会写文件。
