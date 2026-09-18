"""
Safe Read-Only SQLite Reader for Antigravity databases.
Guarantees zero writes (mode=ro, PRAGMA query_only=ON) and handles locked/corrupt files defensibly.
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any, Generator, Tuple


class DatabaseReadError(Exception):
    """Raised when database reading fails due to corruption, missing files, or lock timeouts."""
    pass


class SafeDatabaseReader:
    """
    Context manager for safe, read-only SQLite database inspection and querying.
    """

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

        # Validate non-empty file and magic header
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
            resolved = self.db_path.resolve()
            uri = f"file:///{resolved.as_posix()}?mode=ro"
            self.conn = sqlite3.connect(uri, uri=True, timeout=self.timeout)
            self.conn.execute("PRAGMA query_only = ON;")
            self.conn.execute(f"PRAGMA busy_timeout = {int(self.timeout * 1000)};")
            return self.conn
        except sqlite3.OperationalError as e:
            # Fallback connection without URI if URI mode unsupported on platform
            try:
                self.conn = sqlite3.connect(str(self.db_path), timeout=self.timeout)
                self.conn.execute("PRAGMA query_only = ON;")
                self.conn.execute(f"PRAGMA busy_timeout = {int(self.timeout * 1000)};")
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
            return None
        except sqlite3.Error:
            return None

    def stream_steps(self, chunk_size: int = 200) -> Generator[Tuple[int, int, bytes], None, None]:
        if not self.conn:
            raise DatabaseReadError("Database not connected.")
        cursor = self.conn.cursor()
        cursor.execute("SELECT idx, step_type, step_payload FROM steps ORDER BY idx ASC;")
        while True:
            rows = cursor.fetchmany(chunk_size)
            if not rows:
                break
            for row in rows:
                yield (row[0], row[1], row[2])
