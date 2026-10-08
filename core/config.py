"""
Central configuration for Golden Rules Obsidian (GRO) v3.0 Universal Engine.
Provides path resolution, environment detection, and constants.
100% Zero-Dependency: Uses pure Python standard library only.
"""

from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Optional

# Resolve User Profile across Windows / POSIX
USER_PROFILE = Path(os.environ.get("USERPROFILE", os.path.expanduser("~")))


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
        for v_name in ("vault", "Vault"):
            v_dir = p / v_name
            if v_dir.is_dir():
                if (v_dir / ".obsidian").is_dir() or (v_dir / "00_Meta").is_dir():
                    return v_dir
                # Check 1 level down inside Vault (e.g. Vault/Lemonaru)
                try:
                    for sub in v_dir.iterdir():
                        if sub.is_dir() and ((sub / ".obsidian").is_dir() or (sub / "00_Meta").is_dir()):
                            return sub
                except Exception:
                    pass

    # Check user profile Obsidian vault if it has 00_Meta or .obsidian
    user_vault = USER_PROFILE / "Obsidian" / "Vault"
    if (user_vault / "00_Meta").exists() or (user_vault / ".obsidian").exists():
        return user_vault

    # Check candidate in cwd if it contains 00_Meta
    for name in ("vault", "Vault"):
        candidate = curr / name
        if candidate.is_dir() and ((candidate / ".obsidian").is_dir() or (candidate / "00_Meta").is_dir()):
            return candidate

    for home_candidate in (
        USER_PROFILE / "Documents" / "Obsidian",
        USER_PROFILE / "Obsidian" / "Vault",
    ):
        if home_candidate.exists():
            return home_candidate

    return user_vault


DEFAULT_VAULT_ROOT = find_obsidian_vault()
DEFAULT_LOGS_SUBDIR = os.environ.get("GRO_LOGS_SUBDIR", "Antigravity Logs")
DEFAULT_LOGS_DIR = DEFAULT_VAULT_ROOT / "00_Meta" / DEFAULT_LOGS_SUBDIR
VAULT_LOGS_DIR = DEFAULT_LOGS_DIR
DEFAULT_MAIN_MOC = DEFAULT_LOGS_DIR / "Index - Antigravity Logs.md"
MAIN_MOC_NAME = "Index - Antigravity Logs.md"

# Timezone default
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
