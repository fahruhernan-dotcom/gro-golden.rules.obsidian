"""
Affected File Path Extractor for Antigravity provider.
Extracts reliable file paths from tool calls, arguments, and uri references.
"""

import re
import urllib.parse
from typing import List, Set

TOOL_FILE_PATTERNS = [
    re.compile(r'"(?:TargetFile|AbsolutePath|FilePath|path)"\s*:\s*"([^"]+)"', re.IGNORECASE),
    re.compile(r'file:///(?:[a-zA-Z]:[/\\]|[^\s"\'<>]+)[^\s"\'<>]*', re.IGNORECASE),
]

IGNORE_EXTENSIONS = {
    ".pyc", ".db", ".sqlite", ".sqlite3", ".db-wal", ".db-shm", ".pb", ".png", ".jpg", ".jpeg", ".ico", ".svg"
}


def extract_affected_files(payloads: List[bytes]) -> List[str]:
    """
    Extracts distinct reliable affected file paths from step payloads.
    Returns cleaned, relative or normalized paths suitable for Obsidian wikilinks.
    """
    found: Set[str] = set()

    for payload in payloads:
        if not payload or len(payload) < 10:
            continue

        text = payload.decode("utf-8", errors="ignore")

        for pattern in TOOL_FILE_PATTERNS:
            for match in pattern.finditer(text):
                raw_path = match.group(1) if match.groups() else match.group(0)
                clean_p = raw_path.strip().strip('"\'')

                if clean_p.startswith("file:///"):
                    clean_p = clean_p[8:]

                clean_p = urllib.parse.unquote(clean_p)
                clean_p = clean_p.replace("\\", "/")

                # Strip trailing punctuation often caught from markdown links or logs
                clean_p = clean_p.rstrip(")]}>,\"'*;:! ")
                clean_p = clean_p.strip()

                # Exclude internal / system files
                if any(ignored in clean_p.lower() for ignored in (".gemini", "node_modules", ".git", "scratch/")):
                    continue

                # Exclude regex syntax artifacts or malformed tokens
                if any(bad in clean_p for bad in ("(?:", "[", "]", "*", "|", "<", ">", '"', "'", "\n", "\r", "\t")):
                    continue

                # Exclude non-code assets
                if any(clean_p.lower().endswith(ext) for ext in IGNORE_EXTENSIONS):
                    continue

                # Strip drive letter if present (e.g. C:, D:)
                if len(clean_p) > 2 and clean_p[1] == ":":
                    clean_p = clean_p[2:]
                clean_p = clean_p.lstrip("/")

                # Ensure it looks like a real file with an extension
                if "/" in clean_p and "." in clean_p:
                    ext = clean_p[clean_p.rfind("."):].lower()
                    if len(ext) in (3, 4, 5) and ext.isalnum() or ext in (".ts", ".js", ".py", ".md", ".sh", ".json", ".yaml", ".yml", ".html", ".css", ".toml"):
                        parts = clean_p.split("/")
                        if len(parts) > 3 and parts[0] in ("d:", "c:", "Users", "Dokumen"):
                            clean_p = "/".join(parts[-3:])
                        found.add(clean_p)

    return sorted(list(found))
