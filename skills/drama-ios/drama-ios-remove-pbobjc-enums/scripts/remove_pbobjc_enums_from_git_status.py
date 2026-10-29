#!/usr/bin/env python3
"""基于当前 git status 清理 pbobjc 枚举辅助代码。"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


PB_ROOT_PREFIXES = ("Cores/pbobjc/", "DramaApp/Protos/pbobjc/")
PB_SUFFIXES = (".pbobjc.h", ".pbobjc.m")

HEADER_ENUM_DESCRIPTOR_PATTERN = re.compile(
    r"(?m)^[ \t]*GPBEnumDescriptor \*.*_EnumDescriptor\(void\);\n?"
)
HEADER_ENUM_VALIDATOR_PATTERN = re.compile(
    r"(?m)^[ \t]*BOOL .*_IsValidValue\(int32_t value\);\n?"
)
HEADER_RAW_VALUE_PATTERN = re.compile(
    r"(?m)^[ \t]*(?:int32_t .*_RawValue\(.*\);|void Set.*_RawValue\(.*\);)\n?"
)

SOURCE_ENUM_DESCRIPTOR_PATTERN = re.compile(
    r"^[ \t]*GPBEnumDescriptor \*.*_EnumDescriptor\(void\)\s*\{"
)
SOURCE_ENUM_VALIDATOR_PATTERN = re.compile(
    r"^[ \t]*BOOL .*_IsValidValue\(int32_t value__\)\s*\{"
)
SOURCE_RAW_VALUE_PATTERN = re.compile(
    r"^[ \t]*(?:int32_t .*_RawValue\(.*\)|void Set.*_RawValue\(.*\))\s*\{"
)
PACKAGE_PATTERN = re.compile(r'(?m)^([ \t]*)\.package = ".*",\n')
STRUCT_PATTERN = re.compile(
    r"typedef struct (?P<name>\w+_storage_) \{(?P<body>.*?)\} (?P=name);",
    re.S,
)
ENUM_FIELD_PATTERN = re.compile(
    r"\{(?P<body>.*?)\}",
    re.S,
)
OFFSET_FIELD_PATTERN = re.compile(r"offsetof\([^,]+,\s*(?P<field>\w+)\)")
FLAG_ASSIGNMENT_PATTERN = re.compile(
    r"(?P<prefix>\.flags = \(GPBFieldFlags\)\()(?P<body>[^)]*)(?P<suffix>\),)"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="按当前 git status 清理 pbobjc 枚举辅助代码")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[4],
        help="仓库根目录，默认按脚本位置自动推导",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=None,
        help="显式指定要处理的 pbobjc 文件；为空时读取 git status",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="真正写盘；默认仅预览目标文件",
    )
    return parser.parse_args()


def normalize_relative_path(repo_root: Path, raw_path: str) -> str | None:
    path = raw_path.strip()
    if not path:
        return None
    abs_path = Path(path)
    if abs_path.is_absolute():
        try:
            rel_path = abs_path.relative_to(repo_root)
        except ValueError:
            return None
        normalized = rel_path.as_posix()
    else:
        normalized = Path(path).as_posix()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def should_process(path: str) -> bool:
    return path.endswith(PB_SUFFIXES) and path.startswith(PB_ROOT_PREFIXES)


def read_git_status_paths(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        # git status --short 的前 3 列是状态位，真实路径从第 4 列开始。
        path_text = line[3:]
        if " -> " in path_text:
            path_text = path_text.split(" -> ", 1)[1]
        normalized = normalize_relative_path(repo_root, path_text)
        if normalized is not None:
            paths.append(normalized)
    return paths


def collect_target_files(repo_root: Path, explicit_files: list[str] | None) -> list[Path]:
    if explicit_files:
        raw_paths = explicit_files
    else:
        raw_paths = read_git_status_paths(repo_root)

    targets: list[Path] = []
    seen: set[Path] = set()
    for raw_path in raw_paths:
        normalized = normalize_relative_path(repo_root, raw_path)
        if normalized is None or not should_process(normalized):
            continue
        file_path = repo_root / normalized
        if not file_path.is_file():
            continue
        if file_path not in seen:
            seen.add(file_path)
            targets.append(file_path)
    return sorted(targets)


def remove_patterns(content: str, patterns: list[re.Pattern[str]]) -> tuple[str, int]:
    total = 0
    updated = content
    for pattern in patterns:
        updated, count = pattern.subn("", updated)
        total += count
    return updated, total


def remove_function_blocks(content: str, patterns: list[re.Pattern[str]]) -> tuple[str, int]:
    lines = content.splitlines(keepends=True)
    kept_lines: list[str] = []
    removed = 0
    index = 0

    while index < len(lines):
        line = lines[index]
        if not any(pattern.match(line) for pattern in patterns):
            kept_lines.append(line)
            index += 1
            continue

        removed += 1
        brace_depth = line.count("{") - line.count("}")
        index += 1

        # 按大括号配平删除整个函数块，避免正则跨越后续 message 实现。
        while index < len(lines):
            current = lines[index]
            brace_depth += current.count("{") - current.count("}")
            index += 1
            if brace_depth <= 0:
                break

    return "".join(kept_lines), removed


def extract_enum_storage_fields(content: str) -> set[str]:
    fields: set[str] = set()
    for match in ENUM_FIELD_PATTERN.finditer(content):
        block = match.group("body")
        if ".dataTypeSpecific.enumDescFunc =" not in block:
            continue
        if ".dataType = GPBDataTypeEnum," not in block:
            continue
        # 先从 descriptor 字段里反推出 storage 成员名，再只改这些枚举字段，避免误伤其他类型。
        offset_match = OFFSET_FIELD_PATTERN.search(block)
        if offset_match:
            fields.add(offset_match.group("field"))
    return fields


def rewrite_storage_structs(content: str, field_names: set[str]) -> str:
    if not field_names:
        return content

    def replace_struct(match: re.Match[str]) -> str:
        struct_body = match.group("body")
        updated_body = struct_body
        for field_name in sorted(field_names):
            field_pattern = re.compile(
                rf"(?m)^([ \t]*)(?!int32_t\b)([A-Za-z_]\w*)([ \t]+{re.escape(field_name)};)$"
            )
            updated_body = field_pattern.sub(r"\1int32_t\3", updated_body)
        return match.group(0).replace(struct_body, updated_body)

    return STRUCT_PATTERN.sub(replace_struct, content)


def rewrite_flag_assignments(content: str) -> str:
    def replace_flags(match: re.Match[str]) -> str:
        flags = [item.strip() for item in match.group("body").split("|")]
        flags = [item for item in flags if item and item != "GPBFieldHasEnumDescriptor"]
        return f"{match.group('prefix')}{' | '.join(flags)}{match.group('suffix')}"

    return FLAG_ASSIGNMENT_PATTERN.sub(replace_flags, content)


def rewrite_descriptor_metadata(content: str) -> str:
    updated = re.sub(
        r"\.dataTypeSpecific\.enumDescFunc = [^,]+,",
        ".dataTypeSpecific.clazz = Nil,",
        content,
    )
    updated = rewrite_flag_assignments(updated)
    updated = updated.replace(".dataType = GPBDataTypeEnum,", ".dataType = GPBDataTypeInt32,")
    updated = PACKAGE_PATTERN.sub(r'\1.package = "",' + "\n", updated)
    return updated


def transform_header(content: str) -> tuple[str, dict[str, int]]:
    updated, removed = remove_patterns(
        content,
        [
            HEADER_ENUM_DESCRIPTOR_PATTERN,
            HEADER_ENUM_VALIDATOR_PATTERN,
            HEADER_RAW_VALUE_PATTERN,
        ],
    )
    return updated, {"removed_declarations": removed}


def transform_source(content: str) -> tuple[str, dict[str, int]]:
    enum_fields = extract_enum_storage_fields(content)
    updated, removed = remove_function_blocks(
        content,
        [
            SOURCE_ENUM_DESCRIPTOR_PATTERN,
            SOURCE_ENUM_VALIDATOR_PATTERN,
            SOURCE_RAW_VALUE_PATTERN,
        ],
    )
    updated = rewrite_storage_structs(updated, enum_fields)
    updated = rewrite_descriptor_metadata(updated)
    return updated, {"removed_definitions": removed, "enum_fields": len(enum_fields)}


def process_file(file_path: Path, apply_changes: bool) -> tuple[bool, dict[str, int]]:
    original = file_path.read_text(encoding="utf-8")
    if file_path.suffix == ".h":
        updated, stats = transform_header(original)
    else:
        updated, stats = transform_source(original)

    changed = updated != original
    if changed and apply_changes:
        file_path.write_text(updated, encoding="utf-8")
    return changed, stats


def main() -> int:
    args = parse_args()
    repo_root = args.root.resolve()
    target_files = collect_target_files(repo_root, args.files)

    if not target_files:
        print("未找到需要处理的 pbobjc 变更文件。")
        return 0

    mode = "apply" if args.apply else "dry-run"
    print(f"模式: {mode}")
    print("目标文件:")
    for file_path in target_files:
        print(f"- {file_path.relative_to(repo_root).as_posix()}")

    if not args.apply:
        print("dry-run 模式不会写盘；如需落盘，请追加 --apply。")
        return 0

    changed_files = 0
    for file_path in target_files:
        changed, stats = process_file(file_path, apply_changes=True)
        status = "已更新" if changed else "无需修改"
        rel_path = file_path.relative_to(repo_root).as_posix()
        print(f"{status}: {rel_path} {stats}")
        if changed:
            changed_files += 1

    print(f"完成，共写入 {changed_files} 个文件。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
