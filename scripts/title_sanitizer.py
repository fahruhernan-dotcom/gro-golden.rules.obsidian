"""
Session Title Generator and Windows Filename Sanitizer.
Ensures clean, collision-resistant, and Windows-safe filenames.
"""

import re
from pathlib import Path
from typing import Optional, Any
from config import WINDOWS_RESERVED_NAMES

def sanitize_filename(name: str, max_length: int = 50) -> str:
    r"""
    Sanitizes string for Windows filesystems and Obsidian wikilinks:
    - Removes illegal chars: \ / : * ? " < > |
    - Removes wikilink breaking chars: [ ] @
    - Removes control characters and excess whitespace
    - Handles Windows reserved names (CON, PRN, AUX, NUL, COM1-9, LPT1-9)
    - Strips trailing dots and spaces
    """
    if not name:
        return "Catatan Tanpa Judul"

    # Replace path separators with spaces
    s = name.replace("\\", " ").replace("/", " ")

    # Strip forbidden filesystem and wikilink chars
    s = re.sub(r'[:*?"<>|@\[\]\r\n\t]', ' ', s)

    # Replace multiple spaces with a single space
    s = re.sub(r'\s+', ' ', s).strip()

    # Strip leading/trailing dots and spaces (illegal in Windows)
    s = s.strip(". ").strip()

    if not s:
        s = "Catatan Tanpa Judul"

    # Truncate to max_length without breaking words if possible
    if len(s) > max_length:
        truncated = s[:max_length].strip()
        # if truncated ends mid-word, trim back to last space if reasonable
        if " " in truncated and len(truncated) > 20:
            last_space = truncated.rfind(" ")
            if last_space > 15:
                truncated = truncated[:last_space].strip()
        s = truncated

    # Re-strip trailing dots after truncation
    s = s.rstrip(". ").strip()

    # Check for Windows reserved names
    upper_base = s.upper().split(".")[0]
    if upper_base in WINDOWS_RESERVED_NAMES:
        s = f"{s}_note"

    return s if s else "Catatan Tanpa Judul"


def extract_session_title(
    native_title: Optional[str] = None,
    first_user_prompt: Optional[str] = None,
    fallback: str = "Diskusi Antigravity"
) -> str:
    """
    Resolves session title using precedence:
    1. native_title (if non-empty and not generic)
    2. first_user_prompt (cleaned from tags, boilerplate, and markdown headers)
    3. fallback
    """
    # 1. Native title
    if native_title and len(native_title.strip()) > 3:
        clean_native = sanitize_filename(native_title.strip())
        if clean_native and clean_native.lower() not in ("untitled", "chat", "session", "new chat"):
            return clean_native

    # 2. First user prompt
    if first_user_prompt and len(first_user_prompt.strip()) > 2:
        # Strip system / metadata envelopes
        raw = first_user_prompt.strip()
        # Remove XML tags
        raw = re.sub(r"<[^>]+>", " ", raw)
        lines = [l.strip() for l in raw.splitlines() if len(l.strip()) > 2]
        
        for line in lines:
            # Skip system prompts or greetings
            if any(line.startswith(prefix) for prefix in (
                "Kamu terhubung", "The current local", "User state", "Other open", "Task:"
            )):
                continue
            # Strip markdown headers or list markers
            cleaned_line = re.sub(r'^[#*_\-\s\d\.]+', '', line).strip()
            if len(cleaned_line) >= 4:
                return sanitize_filename(cleaned_line)

    # 3. Fallback
    return sanitize_filename(fallback)


def generate_title_from_prompt(prompt: str, fallback: str = "Diskusi Antigravity") -> str:
    """Convenience alias for extract_session_title using user prompt."""
    return extract_session_title(first_user_prompt=prompt, fallback=fallback)


def make_session_filename(
    date_str: str,
    time_file_part: str,
    title: str,
    suffix: Optional[int] = None
) -> str:
    """
    Builds standard filename: YYYY-MM-DD - HH.mm - Topic.md
    If suffix is provided: YYYY-MM-DD - HH.mm - Topic [2].md
    """
    clean_t = sanitize_filename(title)
    if suffix and suffix > 1:
        base = f"{date_str} - {time_file_part} - {clean_t} [{suffix}].md"
    else:
        base = f"{date_str} - {time_file_part} - {clean_t}.md"
    return base


def generate_session_filename(
    title: str,
    timestamp: Any,
    target_folder: Optional[Path] = None
) -> str:
    """
    Generates a full unique filename given title, timestamp, and optional target_folder.
    """
    from timestamp_parser import parse_timestamp, format_dt
    dt, _ = parse_timestamp(timestamp)
    fdt = format_dt(dt)
    base_name = make_session_filename(fdt["date"], fdt["file_time"], title)
    if not target_folder:
        return base_name

    folder = Path(target_folder)
    target_path = folder / base_name
    counter = 2
    while target_path.exists():
        suffix_name = make_session_filename(fdt["date"], fdt["file_time"], title, suffix=counter)
        target_path = folder / suffix_name
        counter += 1
        if counter > 50:
            break
    return target_path.name
