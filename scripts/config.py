"""
Central configuration for Persistent Obsidian Memory System (Scripts).
Provides path resolution, environment detection, and constants.
Zero hardcoded user or project paths: fully portable across Windows, macOS, and Linux.
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Resolve User Profile across Windows / POSIX
USER_PROFILE = Path(os.environ.get("USERPROFILE", os.path.expanduser("~")))

# Default Storage Root for Antigravity provider
DEFAULT_ANTIGRAVITY_ROOT = USER_PROFILE / ".gemini" / "antigravity-ide"
DEFAULT_CONVERSATIONS_DIR = DEFAULT_ANTIGRAVITY_ROOT / "conversations"


def find_obsidian_vault(start_path: Optional[Path] = None) -> Path:
    """
    Auto-detects Obsidian vault root in order of priority:
    1. Environment variables GRO_VAULT_ROOT or OBSIDIAN_VAULT_ROOT
    2. Walking upwards from start_path (or cwd) searching for .obsidian directory
    3. Checking './vault' or './Vault' in start_path / cwd
    4. Fallback: ~/Documents/Obsidian or ~/Obsidian/Vault
    """
    env_vault = os.environ.get("GRO_VAULT_ROOT") or os.environ.get("OBSIDIAN_VAULT_ROOT")
    if env_vault:
        return Path(env_vault).resolve()

    curr = (start_path or Path.cwd()).resolve()
    for p in [curr] + list(curr.parents):
        if (p / ".obsidian").is_dir():
            return p
        if (p / "vault").is_dir() and (p / "vault" / ".obsidian").is_dir():
            return p / "vault"
        if (p / "Vault").is_dir() and (p / "Vault" / ".obsidian").is_dir():
            return p / "Vault"

    for name in ("vault", "Vault"):
        candidate = curr / name
        if candidate.is_dir():
            return candidate

    for home_candidate in (
        USER_PROFILE / "Documents" / "Obsidian",
        USER_PROFILE / "Obsidian" / "Vault",
    ):
        if home_candidate.exists():
            return home_candidate

    return USER_PROFILE / "Obsidian" / "Vault"


DEFAULT_VAULT_ROOT = find_obsidian_vault()
DEFAULT_LOGS_SUBDIR = os.environ.get("GRO_LOGS_SUBDIR", "Antigravity Logs")
DEFAULT_LOGS_DIR = DEFAULT_VAULT_ROOT / "00_Meta" / DEFAULT_LOGS_SUBDIR
VAULT_LOGS_DIR = DEFAULT_LOGS_DIR
DEFAULT_MAIN_MOC = DEFAULT_LOGS_DIR / "Index - Antigravity Logs.md"
MAIN_MOC_NAME = "Index - Antigravity Logs.md"

# Normalized Intermediate Storage
DEFAULT_NORMALIZED_DIR = Path(__file__).resolve().parent.parent / "normalized"

# Default Timezone
DEFAULT_TIMEZONE = os.environ.get("GRO_TIMEZONE", "Asia/Jakarta")

# Windows Reserved Names
WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
}

# Standard Obsidian Tags
REQUIRED_TAGS = ["type/ai-log", "source/antigravity"]
REQUIRED_HUB_TAGS = ["type/master-hub", "type/moc", "source/antigravity"]
REQUIRED_SUBHUB_TAGS = ["type/sub-hub", "type/moc", "source/antigravity"]
