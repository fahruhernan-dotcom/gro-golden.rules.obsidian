"""
Filename Sanitizer and Session Title Generator.
Ensures clean, collision-resistant, and Windows-safe filenames.
"""

import re
from pathlib import Path
from typing import Optional, Any, List

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
    "bantu saya", "tolong", "cek ini", "apa kabar", "chat", "untitled"
}

SECRET_KEY_PATTERNS = [
    re.compile(r'\bsk-[a-zA-Z0-9_\-]{8,}\b', re.IGNORECASE),
    re.compile(r'\bghp_[a-zA-Z0-9]{20,}\b', re.IGNORECASE),
    re.compile(r'\bbearer\s+[a-zA-Z0-9_\-\.]{15,}\b', re.IGNORECASE),
    re.compile(r'\b[a-f0-9]{32,64}\b', re.IGNORECASE),
]

CLI_COMMAND_PATTERNS = [
    (re.compile(r'gro\s+archive\s+--topic\s+["\']?([^"\'\n]+)["\']?', re.IGNORECASE), r'\1'),
    (re.compile(r'gro\s+watch\s+(?:start|stop|status)', re.IGNORECASE), "Operasi Watcher Background GRO"),
    (re.compile(r'gro\s+validate', re.IGNORECASE), "Audit Validasi Vault"),
    (re.compile(r'gro\s+search\s+["\']?([^"\'\n]+)["\']?', re.IGNORECASE), r'Pencarian Vault - \1'),
    (re.compile(r'gro\s+council\s+.*', re.IGNORECASE), "Musyawarah AI Council"),
    (re.compile(r'gro\s+(?:archive|index)', re.IGNORECASE), "Pengarsipan Sesi GRO"),
    (re.compile(r'(?:py|python)\s+-m\s+pytest.*', re.IGNORECASE), "Eksekusi Pengujian Test Suite"),
    (re.compile(r'git\s+(?:commit|push|pull|status|add|diff).*', re.IGNORECASE), "Operasi Version Control Git"),
]

COLLOQUIAL_PREFIXES = [
    r'^(?:nah|ok|oke|ya|yup|siap|sip)\s*[,.\-]?\s*',
    r'^(?:sekarang|coba|tolong|bantu|bisa|aku mau|saya ingin|mau coba|coba buat)\s+',
    r'^(?:cek|lihat|baca)\s+(?:di\s+)?(?:vault\s+)?(?:tentang\s+|kita\s+)?',
    r'^(?:apa\s+itu|bagaimana\s+cara|gimana\s+caranya)\s+',
    r'^(?:ini\s+dah\s+|apakah\s+ini\s+|apakah\s+)',
    r'^(?:seberapa\s+berguna\s+kalau\s+ini\s+dijadikan\s+)',
]


def clean_semantic_prompt(line: str) -> str:
    """
    Cleans a user prompt line to make it suitable as a semantic note title:
    1. Redacts secrets/API keys.
    2. Resolves CLI commands to human descriptions or extracted topics.
    3. Strips casual conversational filler prefixes.
    4. Trims trailing dangling conjunctions or punctuation.
    """
    if not line:
        return ""

    s = line.strip()

    # 1. CLI Commands
    for pattern, repl in CLI_COMMAND_PATTERNS:
        if pattern.search(s):
            s = pattern.sub(repl, s).strip()
            break

    # 2. Secret / Token redacting
    for sp in SECRET_KEY_PATTERNS:
        if sp.search(s):
            cleaned_of_keys = sp.sub("", s).strip()
            if len(cleaned_of_keys) < 8 or cleaned_of_keys.lower() in ("ini", "key", "api key", "ini kuncinya"):
                return "Konfigurasi Kredensial & Gateway API"
            s = sp.sub("API Key", s).strip()

    # 3. Clean IDE mentions like @[d:\path\to\file] or @[filename] to just filename
    s = re.sub(r'@\[[^\]]*[/\\]([^/\\\]]+)\]', r'\1', s)
    s = re.sub(r'@\[([^\]]+)\]', r'\1', s)

    # 4. Colloquial prefixes
    for cp in COLLOQUIAL_PREFIXES:
        s = re.sub(cp, "", s, flags=re.IGNORECASE).strip()

    # 5. Clean dangling trailing words like 'yg', 'ini', 'itu', 'dan', 'di'
    s = re.sub(r'\s+(?:yg|yang|ini|itu|dan|di|ke|dari|agak|deh)\s*$', '', s, flags=re.IGNORECASE).strip()

    return s


def generate_smart_title_via_llm(user_prompt: str, assistant_snippet: Optional[str] = None) -> Optional[str]:
    """
    Attempts to generate a clean, concise, 3-6 word professional Indonesian title
    using the configured LLM client. Falls back to None if offline or disabled.
    """
    try:
        from core.llm import LLMClient
        client = LLMClient()
        if not client.is_configured():
            return None

        clean_user = user_prompt[:300]
        for sp in SECRET_KEY_PATTERNS:
            clean_user = sp.sub("[KEY]", clean_user)

        prompt_msg = f"User: {clean_user}"
        if assistant_snippet:
            clean_asst = assistant_snippet[:300]
            for sp in SECRET_KEY_PATTERNS:
                clean_asst = sp.sub("[KEY]", clean_asst)
            prompt_msg += f"\nAssistant: {clean_asst}"

        messages = [
            {
                "role": "system",
                "content": (
                    "Anda kurator arsip teknis Obsidian. "
                    "Tugas: Buat 1 judul ringkas (3-6 kata dalam Bahasa Indonesia formal) "
                    "untuk merangkum topik utama pembahasan berikut. "
                    "Aturan: DILARANG menyertakan kata obrolan (seperti 'ok', 'coba', 'halo', 'tanya', 'ini'), "
                    "DILARANG menyertakan perintah terminal mentah atau API key. "
                    "Hanya keluarkan teks judul saja tanpa tanda kutip."
                )
            },
            {
                "role": "user",
                "content": prompt_msg
            }
        ]

        title_res = client.chat(messages=messages, temperature=0.2, max_tokens=30, timeout=3)
        if title_res:
            title_res = title_res.strip().strip('"\'`').rstrip('.')
            if 5 <= len(title_res) <= 60 and not any(bad in title_res.lower() for bad in ("sk-", "http", "curl", "error")):
                return sanitize_filename(title_res)
    except Exception:
        pass
    return None


def extract_session_title(
    native_title: Optional[str] = None,
    first_user_prompt: Optional[str] = None,
    explicit_topic: Optional[str] = None,
    all_user_prompts: Optional[List[str]] = None,
    assistant_reply: Optional[str] = None,
    use_llm: bool = True,
    fallback: str = "Diskusi Antigravity"
) -> str:
    """
    Resolves session title using precedence:
    1. explicit_topic (provided by user or caller with high semantic confidence)
    2. native_title (if non-empty and not generic)
    3. smart LLM title generation (if configured and enabled)
    4. semantic extraction and sanitization from user prompts
    5. fallback
    """
    # 1. Explicit topic
    if explicit_topic and len(explicit_topic.strip()) >= 3:
        clean_exp = clean_semantic_prompt(explicit_topic.strip())
        clean_exp = sanitize_filename(clean_exp)
        if clean_exp and clean_exp.lower() not in ("untitled", "chat", "session"):
            return clean_exp

    # 2. Native title
    if native_title and len(native_title.strip()) > 3:
        clean_native = clean_semantic_prompt(native_title.strip())
        clean_native = sanitize_filename(clean_native)
        if clean_native and clean_native.lower() not in ("untitled", "chat", "session", "new chat"):
            return clean_native

    # Gather substantive prompt candidates
    candidate_prompts = []
    if all_user_prompts:
        candidate_prompts.extend(all_user_prompts)
    elif first_user_prompt:
        candidate_prompts.append(first_user_prompt)

    # 3. Smart LLM Title Generation (if enabled)
    if use_llm and candidate_prompts:
        llm_title = generate_smart_title_via_llm(candidate_prompts[0], assistant_snippet=assistant_reply)
        if llm_title:
            return llm_title

    # 4. Deterministic Heuristic Extraction
    for prompt_text in candidate_prompts:
        if not prompt_text or len(prompt_text.strip()) < 3:
            continue

        raw = re.sub(r"<[^>]+>", " ", prompt_text).strip()
        lines = [l.strip() for l in raw.splitlines() if len(l.strip()) > 2]

        for line in lines:
            if any(line.startswith(prefix) for prefix in (
                "Kamu terhubung", "The current local", "User state", "Other open", "Task:"
            )):
                continue

            cleaned_line = re.sub(r'^[#*_\-\s\d\.]+', '', line).strip()
            if len(cleaned_line) < 3:
                continue

            cleaned_semantic = clean_semantic_prompt(cleaned_line)
            cleaned_lower = cleaned_semantic.lower()

            is_generic = any(starter in cleaned_lower for starter in GENERIC_CONVERSATION_STARTERS)
            if (is_generic or len(cleaned_semantic) < 4) and len(candidate_prompts) > 1:
                continue

            return sanitize_filename(cleaned_semantic)

    # 5. Fallback
    return sanitize_filename(clean_semantic_prompt(fallback))


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
