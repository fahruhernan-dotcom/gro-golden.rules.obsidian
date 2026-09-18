"""
Affected Files Extractor.
Extracts reliable file paths from tool invocations, payloads, and conversation metadata.
"""

import re
from pathlib import Path
from typing import List, Set, Dict, Any, Union

IGNORE_EXTENSIONS = {".tmp", ".temp", ".swp", ".bak", ".db-wal", ".db-shm", ".pyc"}
IGNORE_FILENAMES = {"nul", "con", "null", "undefined", "true", "false", "out.log"}

def extract_affected_files(
    payloads: Union[List[Union[str, bytes]], Dict[str, Any]],
    metadata: Dict[str, Any] = None
) -> List[str]:
    """
    Scans payloads and metadata to extract touched files.
    Returns sorted list of clean, unique file basenames or clean relative paths.
    """
    found: Set[str] = set()

    if isinstance(payloads, (str, bytes)):
        payloads = [payloads]
    elif isinstance(payloads, dict):
        payloads = [str(payloads)]

    for item in payloads:
        if isinstance(item, bytes):
            text = item.decode("utf-8", errors="ignore")
        else:
            text = str(item)

        # 1. Look for TargetFile
        for match in re.findall(r'"TargetFile"\s*:\s*"([^"]+)"', text):
            clean = _clean_filepath(match)
            if clean:
                found.add(clean)

        # 2. Look for AbsolutePath
        for match in re.findall(r'"AbsolutePath"\s*:\s*"([^"]+)"', text):
            clean = _clean_filepath(match)
            if clean:
                found.add(clean)

        # 3. Look for file:// links in text
        for match in re.findall(r'file:///[a-zA-Z]:/[^\s"\'\<\>\)]+', text):
            clean = _clean_filepath(match)
            if clean:
                found.add(clean)

    # 4. Check metadata
    if metadata:
        for k in ("files", "affected_files", "open_documents"):
            v = metadata.get(k)
            if isinstance(v, list):
                for fpath in v:
                    clean = _clean_filepath(str(fpath))
                    if clean:
                        found.add(clean)

    # Filter and sort
    results = sorted(list(found))
    return results[:30]


def _clean_filepath(path_str: str) -> str:
    if not path_str:
        return ""
    # Normalize Windows escapes
    s = path_str.replace("\\\\", "\\").replace("/", "\\")
    s = re.sub(r"^file:\\\\+([a-zA-Z]:)", r"\1", s)
    s = re.sub(r"^file:\\+", "", s)

    p = Path(s)
    name = p.name.strip()
    if not name or len(name) < 3:
        return ""

    # Check ignored
    if p.suffix.lower() in IGNORE_EXTENSIONS:
        return ""
    if name.lower() in IGNORE_FILENAMES:
        return ""
    if name.startswith("task-") and name.endswith(".log"):
        return ""

    return name
