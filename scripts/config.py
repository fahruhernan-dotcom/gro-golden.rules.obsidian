"""
Central configuration for obsidian-vault skill.
Provides robust default path resolution, environment detection, and constants.
"""

import os
import sys
from pathlib import Path

# Resolve User Profile across Windows / POSIX
USER_PROFILE = Path(os.environ.get("USERPROFILE", os.path.expanduser("~")))

# Default Antigravity Storage Root
DEFAULT_ANTIGRAVITY_ROOT = USER_PROFILE / ".gemini" / "antigravity-ide"
DEFAULT_CONVERSATIONS_DIR = DEFAULT_ANTIGRAVITY_ROOT / "conversations"

# Default Obsidian Vault Root for this workspace
DEFAULT_VAULT_ROOT = Path(r"D:\Dokumen\02_Kerja_Profesional\Myself\Vault\Lemonaru")
DEFAULT_LOGS_DIR = DEFAULT_VAULT_ROOT / "00_Meta" / "Antigravity Logs"
VAULT_LOGS_DIR = DEFAULT_LOGS_DIR
DEFAULT_MAIN_MOC = DEFAULT_LOGS_DIR / "Index - Antigravity Logs.md"
MAIN_MOC_NAME = "Index - Antigravity Logs.md"

# Normalized Intermediate Storage
DEFAULT_NORMALIZED_DIR = Path(__file__).resolve().parent.parent / "normalized"

# Default Timezone
DEFAULT_TIMEZONE = "Asia/Jakarta"

# Windows Reserved Names
WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
}

# Required Frontmatter Tags
REQUIRED_TAGS = ["type/ai-log", "source/antigravity"]
REQUIRED_HUB_TAGS = ["type/master-hub", "type/moc", "source/antigravity"]
REQUIRED_SUBHUB_TAGS = ["type/sub-hub", "type/moc", "source/antigravity"]
