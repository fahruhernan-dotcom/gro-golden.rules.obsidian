#!/usr/bin/env python3
"""
Vault Validation CLI Script.
Thin entry point delegating to core VaultValidator.
"""

import sys
import argparse
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add skill directory to sys.path
SKILL_DIR = Path(__file__).resolve().parent.parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from core.config import DEFAULT_LOGS_DIR
from core.validator import VaultValidator, parse_frontmatter, extract_wikilinks


def main():
    parser = argparse.ArgumentParser(description="Validate Obsidian Antigravity Logs structure and integrity.")
    parser.add_argument("--vault", type=str, default=str(DEFAULT_LOGS_DIR), help="Path to Antigravity Logs folder")
    args = parser.parse_args()

    validator = VaultValidator(Path(args.vault))
    is_valid = validator.validate()
    print(validator.format_report())
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
