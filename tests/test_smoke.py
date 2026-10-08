"""
Zero-Dependency Smoke Test Suite for Golden Rules Obsidian (GRO) v3.0.
Uses pure Python standard library (unittest) - no external packages required.
"""

import sys
import unittest
from pathlib import Path

from core.sanitizer import sanitize_filename
from core.config import WINDOWS_RESERVED_NAMES, find_obsidian_vault
from core.cli import VERSION, main, resolve_current_workspace


class TestGROSmoke(unittest.TestCase):
    def test_version(self):
        """Verify version constant is 3.0.0."""
        self.assertEqual(VERSION, "3.0.0")

    def test_sanitizer_illegal_characters(self):
        """Verify Windows illegal characters are stripped from note titles."""
        raw_title = 'Fix: Auth issue <v2> | & "broken" [test]?'
        clean = sanitize_filename(raw_title)
        for char in r'\/:*?"<>|[]@':
            self.assertNotIn(char, clean)

    def test_sanitizer_length_limit(self):
        """Verify filenames are cleanly truncated to safe lengths."""
        long_title = "A" * 120
        clean = sanitize_filename(long_title, max_length=50)
        self.assertLessEqual(len(clean), 50)

    def test_config_reserved_names(self):
        """Verify Windows reserved filenames are tracked."""
        self.assertIn("CON", WINDOWS_RESERVED_NAMES)
        self.assertIn("NUL", WINDOWS_RESERVED_NAMES)
        self.assertIn("COM1", WINDOWS_RESERVED_NAMES)

    def test_workspace_resolution(self):
        """Verify workspace resolution picks valid folder names."""
        dummy_path = Path("/workspace/my-cool-project/core")
        resolved = resolve_current_workspace(dummy_path)
        self.assertEqual(resolved, "my-cool-project")

    def test_cli_version_flag(self):
        """Verify CLI --version exits cleanly with code 0."""
        with self.assertRaises(SystemExit) as cm:
            main(["--version"])
        self.assertEqual(cm.exception.code, 0)

    def test_cli_help_flag(self):
        """Verify CLI --help exits cleanly with code 0."""
        with self.assertRaises(SystemExit) as cm:
            main(["--help"])
        self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
