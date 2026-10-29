#!/usr/bin/env python3

import argparse
import hashlib
import json
import sys
from pathlib import Path


IGNORED_NAMES = {".DS_Store"}


def collect_input_files(design_dir: Path) -> list[Path]:
    if not design_dir.exists():
        raise ValueError(f"design directory does not exist: {design_dir}")
    if not design_dir.is_dir():
        raise ValueError(f"design path is not a directory: {design_dir}")

    files = []
    for path in design_dir.rglob("*"):
        relative_path = path.relative_to(design_dir)
        if any(part.startswith(".") for part in relative_path.parts):
            continue
        if path.name in IGNORED_NAMES or path.is_symlink() or not path.is_file():
            continue
        files.append(path)

    files.sort(key=lambda path: path.relative_to(design_dir).as_posix())
    if not files:
        raise ValueError(f"design directory contains no input files: {design_dir}")
    return files


def calculate_fingerprint(design_dir: Path) -> tuple[str, list[dict[str, object]]]:
    files = collect_input_files(design_dir)
    digest = hashlib.sha256()
    manifest = []

    for path in files:
        relative_path = path.relative_to(design_dir).as_posix()
        relative_bytes = relative_path.encode("utf-8")
        file_size = path.stat().st_size

        digest.update(len(relative_bytes).to_bytes(8, "big"))
        digest.update(relative_bytes)
        digest.update(file_size.to_bytes(8, "big"))

        read_size = 0
        with path.open("rb") as file_handle:
            while True:
                chunk = file_handle.read(1024 * 1024)
                if not chunk:
                    break
                read_size += len(chunk)
                digest.update(chunk)

        if read_size != file_size:
            raise OSError(f"file changed while hashing: {path}")
        manifest.append({"path": relative_path, "size": file_size})

    return digest.hexdigest(), manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate a deterministic fingerprint for design_images inputs."
    )
    parser.add_argument("design_dir", type=Path, help="Path to the design_images directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        fingerprint, manifest = calculate_fingerprint(args.design_dir)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2

    result = {
        "design_dir": str(args.design_dir.resolve()),
        "fingerprint": fingerprint,
        "files": manifest,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
