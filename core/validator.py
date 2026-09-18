"""
Vault Integrity Validation Engine.
Verifies MOC structure, YAML frontmatter, filenames, duplicate conversation IDs, and links.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Any, Tuple, Optional

try:
    from .config import DEFAULT_LOGS_DIR, MAIN_MOC_NAME, REQUIRED_TAGS
    from .models import ValidationReport
except ImportError:
    try:
        from core.config import DEFAULT_LOGS_DIR, MAIN_MOC_NAME, REQUIRED_TAGS
        from core.models import ValidationReport
    except ImportError:
        from config import DEFAULT_LOGS_DIR, MAIN_MOC_NAME, REQUIRED_TAGS
        from models import ValidationReport

FILENAME_RE = re.compile(r'^\d{4}-\d{2}-\d{2}\s*-\s*\d{2}\.\d{2}\s*-\s*.+\.md$')


def extract_wikilinks(text: str) -> List[str]:
    """Extract wikilink targets safely, balancing square brackets."""
    links = []
    for match in re.finditer(r'\[\[(.*?)\]\]', text):
        target = match.group(1).split("|")[0].strip()
        if target.count("[") > target.count("]"):
            target += "]" * (target.count("[") - target.count("]"))
        links.append(target)
    return links


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], bool]:
    """Parse YAML frontmatter between --- and --- without requiring PyYAML."""
    if not content.startswith("---"):
        return {}, False

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, False

    yaml_text = parts[1]
    metadata = {}
    current_key = None
    list_mode = False

    for line in yaml_text.splitlines():
        line_clean = line.strip()
        if not line_clean or line_clean.startswith("#"):
            continue

        if line.startswith("  - ") or line.startswith("    - "):
            if current_key and list_mode:
                val = line_clean[2:].strip().strip('"\'')
                metadata[current_key].append(val)
            continue

        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"\'')
            current_key = key
            if not val:
                metadata[key] = []
                list_mode = True
            else:
                list_mode = False
                metadata[key] = val

    return metadata, True


class VaultValidator:
    def __init__(self, logs_dir: Optional[Path] = None):
        self.logs_dir = Path(logs_dir) if logs_dir else DEFAULT_LOGS_DIR
        self.main_moc_path = self.logs_dir / MAIN_MOC_NAME
        self.issues: List[str] = []
        self.warnings: List[str] = []

        self.total_notes = 0
        self.workspaces_count = 0
        self.broken_links = 0
        self.duplicate_conv_ids = 0
        self.invalid_frontmatter = 0
        self.invalid_filenames = 0
        self.missing_transcripts = 0

    def validate(self) -> bool:
        if not self.logs_dir.exists():
            self.issues.append(f"Logs directory does not exist: {self.logs_dir}")
            return False

        # 1. Main MOC check
        main_moc_exists = self.main_moc_path.exists()
        if not main_moc_exists:
            self.issues.append(f"Main MOC missing: {self.main_moc_path.name}")

        ws_dirs = [d for d in self.logs_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
        self.workspaces_count = len(ws_dirs)

        workspace_mocs: Dict[str, Path] = {}
        all_note_basenames: Set[str] = set()
        seen_conv_ids: Dict[str, Path] = {}
        seen_identities: Dict[str, Path] = {}

        # 2. Check each workspace
        for ws_dir in ws_dirs:
            ws_name = ws_dir.name
            ws_moc_path = ws_dir / f"Index - {ws_name}.md"
            if not ws_moc_path.exists():
                index_candidates = list(ws_dir.glob("Index - *.md"))
                if index_candidates:
                    ws_moc_path = index_candidates[0]
                else:
                    self.issues.append(f"Workspace '{ws_name}' is missing MOC index")

            if ws_moc_path.exists():
                workspace_mocs[ws_name] = ws_moc_path

            note_files = [f for f in ws_dir.glob("*.md") if f.name != ws_moc_path.name]
            self.total_notes += len(note_files)

            for note in note_files:
                all_note_basenames.add(note.stem)

                if not FILENAME_RE.match(note.name):
                    self.invalid_filenames += 1
                    self.warnings.append(f"Filename does not match standard pattern: {note.name}")

                try:
                    content = note.read_text(encoding="utf-8", errors="replace")
                except Exception as e:
                    self.invalid_frontmatter += 1
                    self.issues.append(f"Cannot read note {note}: {e}")
                    continue

                metadata, valid_yaml = parse_frontmatter(content)
                if not valid_yaml:
                    self.invalid_frontmatter += 1
                    self.issues.append(f"Invalid or missing YAML frontmatter: {note.name}")
                else:
                    tags = metadata.get("tags", [])
                    if isinstance(tags, str):
                        tags = [tags]
                    for req_tag in REQUIRED_TAGS:
                        if req_tag not in tags:
                            self.warnings.append(f"Note {note.name} missing required tag: '{req_tag}'")

                    conv_id = metadata.get("conversation_id")
                    if conv_id:
                        part_num = metadata.get("part")
                        conv_key = f"{conv_id}#part{part_num}" if part_num else conv_id
                        if conv_key in seen_conv_ids:
                            self.duplicate_conv_ids += 1
                            self.issues.append(
                                f"Duplicate conversation_id '{conv_id}' (part {part_num}) in {note.name} (already in {seen_conv_ids[conv_key].name})"
                            )
                        else:
                            seen_conv_ids[conv_key] = note

                    date_val = metadata.get("date", "")
                    time_val = metadata.get("time", "")
                    session_key = f"{ws_name}|{date_val}|{time_val}|{note.stem}"
                    if session_key in seen_identities:
                        self.warnings.append(f"Duplicate session identity detected: {note.name}")
                    else:
                        seen_identities[session_key] = note

                if not any(k in content for k in ("Transkrip Dialog Lengkap", "Transkrip Dialog", "Riwayat Dialog", "Transkrip Sesi")):
                    self.missing_transcripts += 1
                    self.warnings.append(f"Note {note.name} might be missing folded transcript callout")

        # 3. Main MOC check: only points to workspace MOCs
        if main_moc_exists:
            main_content = self.main_moc_path.read_text(encoding="utf-8", errors="replace")
            main_links = extract_wikilinks(main_content)
            for target in main_links:
                if target in ("Index - Antigravity Logs", "Index - [Workspace]"):
                    continue
                if not target.startswith("Index -"):
                    self.issues.append(f"Main MOC illegally links directly to non-MOC note: [[{target}]]")
                    self.broken_links += 1
                else:
                    target_filename = f"{target}.md"
                    target_exists = any((ws_dir / target_filename).exists() for ws_dir in ws_dirs)
                    if not target_exists:
                        self.broken_links += 1
                        self.issues.append(f"Main MOC links to non-existent index: [[{target}]]")

        # 4. Workspace MOCs link checks
        for ws_name, ws_moc_path in workspace_mocs.items():
            moc_content = ws_moc_path.read_text(encoding="utf-8", errors="replace")
            ws_links = extract_wikilinks(moc_content)
            for target in ws_links:
                if target == "Index - Antigravity Logs":
                    continue
                target_note_path = ws_moc_path.parent / f"{target}.md"
                if not target_note_path.exists() and target not in all_note_basenames:
                    self.broken_links += 1
                    self.issues.append(f"Workspace MOC '{ws_moc_path.name}' links to missing note: [[{target}]]")

        return len(self.issues) == 0

    def validate_all(self) -> ValidationReport:
        """Runs validation and returns structured ValidationReport dataclass."""
        is_valid = self.validate()
        status = "PASS" if is_valid else "FAIL"
        return ValidationReport(
            status=status,
            total_notes=self.total_notes,
            total_workspaces=self.workspaces_count,
            valid_frontmatter=max(0, self.total_notes - self.invalid_frontmatter),
            broken_links=self.broken_links,
            duplicate_conversation_ids=[],
            missing_transcripts=self.missing_transcripts,
            issues=self.issues,
            warnings=self.warnings
        )

    def format_report(self) -> str:
        status = "PASS" if len(self.issues) == 0 else "FAIL"
        lines = [
            "=== VAULT VALIDATION ===",
            "",
            f"Notes: {self.total_notes}",
            f"Workspaces: {self.workspaces_count}",
            f"Broken links: {self.broken_links}",
            f"Duplicate conversations: {self.duplicate_conv_ids}",
            f"Invalid frontmatter: {self.invalid_frontmatter}",
            f"Invalid filenames: {self.invalid_filenames}",
            f"Missing transcripts: {self.missing_transcripts}",
            "",
            f"STATUS: {status}"
        ]
        if self.issues:
            lines.append("\nIssues:")
            for issue in self.issues[:20]:
                lines.append(f"  - ❌ {issue}")
            if len(self.issues) > 20:
                lines.append(f"  ... and {len(self.issues) - 20} more issues")

        if self.warnings:
            lines.append("\nWarnings:")
            for warning in self.warnings[:15]:
                lines.append(f"  - ⚠️ {warning}")
            if len(self.warnings) > 15:
                lines.append(f"  ... and {len(self.warnings) - 15} more warnings")

        return "\n".join(lines)
