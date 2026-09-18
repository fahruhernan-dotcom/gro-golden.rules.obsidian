"""
Safe Read-Only SQLite Database Reader for Antigravity Conversation Stores.
Enforces strict read-only mode, handles locks, corruption, and schema variances.
"""

import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Generator

class DatabaseReadError(Exception):
    pass

class SafeDatabaseReader:
    def __init__(self, db_path: Path, timeout: float = 5.0):
        self.db_path = Path(db_path)
        self.timeout = timeout
        self.conn: Optional[sqlite3.Connection] = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self) -> sqlite3.Connection:
        if not self.db_path.exists():
            raise DatabaseReadError(f"Database file not found: {self.db_path}")

        # Validate non-empty file
        try:
            if self.db_path.stat().st_size == 0:
                raise DatabaseReadError(f"Database file is empty (0 bytes): {self.db_path.name}")
            with open(self.db_path, "rb") as f:
                header = f.read(16)
                if not header.startswith(b"SQLite format 3\x00"):
                    raise DatabaseReadError(f"File is not a valid SQLite database (corrupt header): {self.db_path.name}")
        except OSError as e:
            raise DatabaseReadError(f"Cannot read database file {self.db_path.name}: {e}")

        try:
            # Connect strictly in read-only mode using URI
            # On Windows: uri=True with file:///path?mode=ro
            resolved = self.db_path.resolve()
            uri = f"file:///{resolved.as_posix()}?mode=ro"
            self.conn = sqlite3.connect(uri, uri=True, timeout=self.timeout)
            # Enforce read-only pragmas
            self.conn.execute("PRAGMA query_only = ON;")
            return self.conn
        except sqlite3.OperationalError as e:
            # Fallback if URI mode fails
            try:
                self.conn = sqlite3.connect(str(self.db_path), timeout=self.timeout)
                self.conn.execute("PRAGMA query_only = ON;")
                return self.conn
            except sqlite3.Error as fallback_err:
                raise DatabaseReadError(f"Failed to open database {self.db_path.name}: {fallback_err}") from e

    def close(self):
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None

    def list_tables(self) -> List[str]:
        if not self.conn:
            raise DatabaseReadError("Database not connected.")
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [row[0] for row in cursor.fetchall()]

    def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        if not self.conn:
            raise DatabaseReadError("Database not connected.")
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        # cid, name, type, notnull, dflt_value, pk
        return [
            {"cid": r[0], "name": r[1], "type": r[2], "notnull": bool(r[3]), "pk": bool(r[5])}
            for r in cursor.fetchall()
        ]

    def read_trajectory_metadata_blob(self) -> Optional[bytes]:
        if not self.conn:
            return None
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT data FROM trajectory_metadata_blob WHERE id = 'main';")
            row = cursor.fetchone()
            return row[0] if row else None
        except sqlite3.Error:
            return None

    def read_trajectory_meta(self) -> Optional[Dict[str, Any]]:
        if not self.conn:
            return None
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT trajectory_id, cascade_id, trajectory_type, source FROM trajectory_meta LIMIT 1;")
            row = cursor.fetchone()
            if row:
                return {
                    "trajectory_id": row[0],
                    "cascade_id": row[1],
                    "trajectory_type": row[2],
                    "source": row[3]
                }
        except sqlite3.Error:
            pass
        return None

    def stream_steps(self, chunk_size: int = 100) -> Generator[Tuple[int, int, bytes], None, None]:
        """
        Streams steps in chunks to prevent high memory usage on large databases.
        Yields (idx, step_type, step_payload).
        """
        if not self.conn:
            return
        cursor = self.conn.cursor()
        offset = 0
        while True:
            cursor.execute(
                "SELECT idx, step_type, step_payload FROM steps ORDER BY idx LIMIT ? OFFSET ?;",
                (chunk_size, offset)
            )
            rows = cursor.fetchall()
            if not rows:
                break
            for r in rows:
                yield (r[0], r[1], r[2])
            offset += len(rows)
