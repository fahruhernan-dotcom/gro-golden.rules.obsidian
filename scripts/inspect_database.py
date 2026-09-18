"""
Database Inspector for Antigravity SQLite Databases.
Read-only schema and payload diagnostic tool.
"""

import sys
import json
import argparse
import sqlite3
from pathlib import Path
from typing import Dict, Any, List

# Ensure skill directory in sys.path
SKILL_DIR = Path(__file__).resolve().parent.parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from core.config import DEFAULT_CONVERSATIONS_DIR
from providers.antigravity.sqlite import SafeDatabaseReader, DatabaseReadError
from providers.antigravity.provider import AntigravityHistoryProvider

def inspect_database(db_path: Path, json_output: bool = False) -> Dict[str, Any]:
    db_file = Path(db_path)
    result = {
        "file": str(db_file),
        "name": db_file.name,
        "exists": db_file.exists(),
        "is_sqlite": False,
        "readable": False,
        "error": None,
        "tables": {},
        "detected_fields": {
            "conversation_id": False,
            "workspace": False,
            "timestamps": False,
            "steps_messages": False,
            "blob_columns": [],
            "text_columns": []
        },
        "stats": {}
    }

    if not db_file.exists():
        result["error"] = "File does not exist"
        _print_result(result, json_output)
        return result

    # Check magic header for SQLite (first 16 bytes: 'SQLite format 3\000')
    try:
        with open(db_file, "rb") as f:
            header = f.read(16)
            if header.startswith(b"SQLite format 3\x00"):
                result["is_sqlite"] = True
            else:
                result["error"] = "Not a valid SQLite file header"
                _print_result(result, json_output)
                return result
    except Exception as e:
        result["error"] = f"Permission denied or read error: {e}"
        _print_result(result, json_output)
        return result

    try:
        with SafeDatabaseReader(db_file) as reader:
            result["readable"] = True
            tables = reader.list_tables()

            for tbl in tables:
                cols = reader.get_table_columns(tbl)
                result["tables"][tbl] = cols

                # Scan column properties
                for c in cols:
                    cname = c["name"].lower()
                    ctype = c["type"].upper()

                    if "BLOB" in ctype or cname in ("step_payload", "data", "metadata"):
                        result["detected_fields"]["blob_columns"].append(f"{tbl}.{c['name']}")
                    if "TEXT" in ctype or "CHAR" in ctype or cname in ("id", "title", "source"):
                        result["detected_fields"]["text_columns"].append(f"{tbl}.{c['name']}")

                    if "trajectory" in cname or "conversation" in cname or "cascade" in cname:
                        result["detected_fields"]["conversation_id"] = True
                    if "workspace" in cname:
                        result["detected_fields"]["workspace"] = True
                    if "time" in cname or "date" in cname or "started" in cname or "ended" in cname:
                        result["detected_fields"]["timestamps"] = True
                    if tbl == "steps":
                        result["detected_fields"]["steps_messages"] = True

            # Collect basic row counts safely
            cursor = reader.conn.cursor()
            for tbl in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
                    result["stats"][tbl] = cursor.fetchone()[0]
                except sqlite3.Error:
                    result["stats"][tbl] = -1

            # Check if trajectory_metadata_blob has workspace information
            blob = reader.read_trajectory_metadata_blob()
            if blob and (b"file:///" in blob or b"workspace" in blob or b"Dokumen" in blob):
                result["detected_fields"]["workspace"] = True

    except DatabaseReadError as e:
        result["error"] = str(e)
    except Exception as e:
        result["error"] = f"Unexpected inspection error: {e}"

    _print_result(result, json_output)
    return result


def _print_result(res: Dict[str, Any], json_output: bool):
    if json_output:
        print(json.dumps(res, indent=2))
        return

    print("=== DATABASE INSPECTOR ===")
    print(f"File: {res['name']}")
    print(f"Path: {res['file']}")
    print(f"Is SQLite: {res['is_sqlite']} | Readable: {res['readable']}")
    if res['error']:
        print(f"Status: ERROR ({res['error']})")
        return

    print("\nTables & Rows:")
    for tbl, cols in res["tables"].items():
        count = res["stats"].get(tbl, 0)
        col_names = ", ".join(c["name"] for c in cols)
        print(f"  - {tbl} ({count} rows): [{col_names}]")

    print("\nDetected Schema Capabilities:")
    df = res["detected_fields"]
    print(f"  - Conversation IDs: {df['conversation_id']}")
    print(f"  - Workspace Metadata: {df['workspace']}")
    print(f"  - Timestamps: {df['timestamps']}")
    print(f"  - Steps/Messages: {df['steps_messages']}")
    print(f"  - BLOB Storage Columns ({len(df['blob_columns'])}): {', '.join(df['blob_columns'][:4])}")
    print("\nStatus: HEALTHY (Safe to extract)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect Antigravity SQLite database.")
    parser.add_argument("path", nargs="?", default=None, help="Path to database file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    target_path = None
    if args.path:
        target_path = Path(args.path)
    else:
        # Default to latest DB
        dbs = sorted(DEFAULT_CONVERSATIONS_DIR.glob("*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
        if dbs:
            target_path = dbs[0]

    if not target_path:
        print("No database specified or found.")
        sys.exit(1)

    inspect_database(target_path, json_output=args.json)
