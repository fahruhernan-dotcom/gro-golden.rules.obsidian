"""
Filename Sanitizer and Session Title Generator.
Ensures clean, collision-resistant, and Windows-safe filenames.
"""

import re
from pathlib import Path
from typing import Optional, Any

try:
    from .config import WINDOWS_RESERVED_NAMES
except ImportError:
    WINDOWS_RESERVED_NAMES = {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
    }


def sanitize_filename(name: str, max_length: int = 80) -> str:
    r"""
    Sanitizes string for Windows filesystems and Obsidian wikilinks:
    - Removes illegal chars: \ / : * ? " < > |
    - Removes wikilink breaking chars: [ ] @
    - Removes control characters and excess whitespace
    - Handles Windows reserved names
    - Strips trailing dots, spaces, and hanging conjunctions/symbols
    """
    if not name:
        return "Catatan Tanpa Judul"

    s = name.strip()

    # Normalize Windows backslashes and slashes to space first
    s = s.replace("\\", " ").replace("/", " ")

    # Remove illegal chars for Windows filesystem & Obsidian wikilinks
    s = re.sub(r'[\/:*?"<>|@\[\]]', ' ', s)

    # Remove control characters
    s = re.sub(r'[\x00-\x1f\x7f]', '', s)

    # Collapse multiple whitespace
    s = re.sub(r'\s+', ' ', s).strip()

    # Truncate to max_length without breaking words awkwardly
    if len(s) > max_length:
        truncated = s[:max_length]
        last_space = truncated.rfind(' ')
        if last_space > max_length // 2:
            s = truncated[:last_space].strip()
        else:
            s = truncated.strip()

    # Strip trailing punctuation, spaces, and hanging symbols (e.g. trailing &, -, dots)
    s = re.sub(r'[\s\.\-_&,;:]+$', '', s).strip()

    # Check for Windows reserved names
    upper_base = s.upper().split('.')[0]
    if upper_base in WINDOWS_RESERVED_NAMES:
        s = f"_{s}"

    return s if s else "Catatan Tanpa Judul"


GENERIC_CONVERSATION_STARTERS = {
    "cek vault", "sampai mana", "tadi sampai mana", "halo", "hello", "hi",
    "pagi", "siang", "sore", "malam", "tes", "test", "lanjut", "bisa bantu",
    "bantu saya", "tolong", "cek ini", "apa kabar"
}


def extract_session_title(
    native_title: Optional[str] = None,
    first_user_prompt: Optional[str] = None,
    explicit_topic: Optional[str] = None,
    all_user_prompts: Optional[List[str]] = None,
    fallback: str = "Diskusi Antigravity"
) -> str:
    """
    Resolves session title using precedence:
    1. explicit_topic (provided by user or caller with high semantic confidence)
    2. native_title (if non-empty and not generic)
    3. semantic extraction from user prompts (filtering out conversational starters)
    4. fallback
    """
    # 1. Explicit topic
    if explicit_topic and len(explicit_topic.strip()) >= 3:
        clean_exp = sanitize_filename(explicit_topic.strip())
        if clean_exp and clean_exp.lower() not in ("untitled", "chat", "session"):
            return clean_exp

    # 2. Native title
    if native_title and len(native_title.strip()) > 3:
        clean_native = sanitize_filename(native_title.strip())
        if clean_native and clean_native.lower() not in ("untitled", "chat", "session", "new chat"):
            return clean_native

    # 3. User prompts (scan first prompt or subsequent substantive prompts)
    candidate_prompts = []
    if all_user_prompts:
        candidate_prompts.extend(all_user_prompts)
    elif first_user_prompt:
        candidate_prompts.append(first_user_prompt)

    for prompt_text in candidate_prompts:
        if not prompt_text or len(prompt_text.strip()) < 3:
            continue

        raw = re.sub(r"<[^>]+>", " ", prompt_text).strip()
        lines = [l.strip() for l in raw.splitlines() if len(l.strip()) > 2]

        for line in lines:
            # Skip system headers
            if any(line.startswith(prefix) for prefix in (
                "Kamu terhubung", "The current local", "User state", "Other open", "Task:"
            )):
                continue

            cleaned_line = re.sub(r'^[#*_\-\s\d\.]+', '', line).strip()
            if len(cleaned_line) < 4:
                continue

            # Check if this is a generic starter (e.g. "cek vault kita tadi sampai mana")
            cleaned_lower = cleaned_line.lower()
            is_generic = any(starter in cleaned_lower for starter in GENERIC_CONVERSATION_STARTERS)
            if is_generic and len(candidate_prompts) > 1:
                # Skip to next prompt to find substantive subject
                continue

            return sanitize_filename(cleaned_line)

    # 4. Fallback
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
    from .timestamp import parse_timestamp, format_dt
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
