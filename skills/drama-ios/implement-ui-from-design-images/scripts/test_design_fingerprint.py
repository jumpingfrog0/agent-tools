#!/usr/bin/env python3

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("design_fingerprint.py")
SPEC = importlib.util.spec_from_file_location("design_fingerprint", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class DesignFingerprintTests(unittest.TestCase):
    def test_fingerprint_is_stable_across_mtime_changes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            design_dir = Path(directory)
            image_path = design_dir / "page.png"
            image_path.write_bytes(b"page")

            first, _ = MODULE.calculate_fingerprint(design_dir)
            os.utime(image_path, (1_000_000, 1_000_000))
            second, _ = MODULE.calculate_fingerprint(design_dir)

            self.assertEqual(first, second)

    def test_content_change_updates_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            design_dir = Path(directory)
            image_path = design_dir / "page.png"
            image_path.write_bytes(b"before")
            before, _ = MODULE.calculate_fingerprint(design_dir)

            image_path.write_bytes(b"after")
            after, _ = MODULE.calculate_fingerprint(design_dir)

            self.assertNotEqual(before, after)

    def test_relative_path_change_updates_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            design_dir = Path(directory)
            first_path = design_dir / "first.png"
            first_path.write_bytes(b"same")
            before, _ = MODULE.calculate_fingerprint(design_dir)

            first_path.rename(design_dir / "second.png")
            after, _ = MODULE.calculate_fingerprint(design_dir)

            self.assertNotEqual(before, after)

    def test_icons_are_included_and_manifest_is_sorted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            design_dir = Path(directory)
            icons_dir = design_dir / "icons"
            icons_dir.mkdir()
            (icons_dir / "b.png").write_bytes(b"b")
            (design_dir / "a.png").write_bytes(b"a")

            _, manifest = MODULE.calculate_fingerprint(design_dir)

            self.assertEqual([item["path"] for item in manifest], ["a.png", "icons/b.png"])

    def test_hidden_files_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            design_dir = Path(directory)
            (design_dir / "page.png").write_bytes(b"page")
            before, manifest = MODULE.calculate_fingerprint(design_dir)

            (design_dir / ".DS_Store").write_bytes(b"noise")
            hidden_dir = design_dir / ".cache"
            hidden_dir.mkdir()
            (hidden_dir / "state").write_bytes(b"noise")
            after, new_manifest = MODULE.calculate_fingerprint(design_dir)

            self.assertEqual(before, after)
            self.assertEqual(manifest, new_manifest)

    def test_missing_and_empty_directories_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                MODULE.collect_input_files(root / "missing")
            with self.assertRaises(ValueError):
                MODULE.collect_input_files(root)


if __name__ == "__main__":
    unittest.main()
