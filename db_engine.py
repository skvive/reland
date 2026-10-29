"""SQLite (local) or Neon Postgres (production) with minimal SQL adaptation."""
from __future__ import annotations

import os
import re
import sqlite3
from contextlib import contextmanager
from typing import Any

DATABASE_URL = (
    os.getenv("DATABASE_URL", "").strip()
    or os.getenv("NEON_DATABASE_URL", "").strip()
)
USE_POSTGRES = DATABASE_URL.startswith(("postgres://", "postgresql://"))


def _adapt_sql(sql: str) -> str:
    if not USE_POSTGRES:
        return sql
    s = sql
    s = re.sub(r"\bINSERT OR IGNORE\b", "INSERT", s, flags=re.I)
    s = s.replace("?", "%s")
    s = re.sub(r"DATE\s*\(\s*'now'\s*\)", "CURRENT_DATE", s, flags=re.I)
    s = re.sub(r"CURRENT_TIMESTAMP", "NOW()", s, flags=re.I)
    if re.search(r"^INSERT\b", s.strip(), re.I) and "ON CONFLICT" not in s.upper():
        if "reports(post_id,user_id" in s.replace(" ", ""):
            s = s.rstrip().rstrip(";") + " ON CONFLICT (post_id, user_id) DO NOTHING"
        elif "news(title,url" in s.replace(" ", ""):
            s = s.rstrip().rstrip(";") + " ON CONFLICT (url) DO NOTHING"
        elif "users(google_sub" in s.replace(" ", ""):
            s = s.rstrip().rstrip(";") + " ON CONFLICT (google_sub) DO NOTHING"
    return s


class _Row(dict):
    def __getitem__(self, key: Any):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


class CompatCursor:
    def __init__(self, raw, is_pg: bool):
        self._raw = raw
        self._is_pg = is_pg
        self._lastrowid: int | None = None

    _NO_RETURNING = (
        "settings",
        "sessions",
        "follows",
        "likes",
        "bookmarks",
        "district_watches",
        "district_geometries",
    )

    def _needs_returning(self, sql: str) -> bool:
        lower = sql.lower()
        if not lower.strip().startswith("insert"):
            return False
        for name in self._NO_RETURNING:
            if f"insert into {name}" in lower:
                return False
        return True

    def execute(self, sql: str, params: tuple | list = ()):
        adapted = _adapt_sql(sql)
        returning = self._is_pg and self._needs_returning(adapted) and "RETURNING" not in adapted.upper()
        if returning:
            if adapted.rstrip().endswith(";"):
                adapted = adapted.rstrip()[:-1]
            adapted = adapted + " RETURNING id"
        self._raw.execute(adapted, params)
        if returning:
            row = self._raw.fetchone()
            self._lastrowid = row[0] if row else None
        else:
            self._lastrowid = None
        return self

    def executemany(self, sql: str, seq):
        self._raw.executemany(_adapt_sql(sql), seq)
        return self

    def executescript(self, script: str):
        if not USE_POSTGRES:
            self._raw.executescript(script)
            return self
        stmts = []
        buf: list[str] = []
        for line in script.splitlines():
            stripped = line.strip()
            if stripped.startswith("PRAGMA"):
                continue
            buf.append(line)
            if ";" in line:
                chunk = "\n".join(buf)
                buf = []
                for part in chunk.split(";"):
                    part = part.strip()
                    if not part:
                        continue
                    stmts.append(_adapt_pg_ddl(part))
        for stmt in stmts:
            self._raw.execute(stmt)
        return self

    def fetchone(self):
        row = self._raw.fetchone()
        if row is None:
            return None
        if self._is_pg:
            cols = [d.name if hasattr(d, "name") else d[0] for d in self._raw.description]
            return _Row(zip(cols, row))
        return row

    def fetchall(self):
        rows = self._raw.fetchall()
        if not self._is_pg:
            return rows
        cols = [d.name if hasattr(d, "name") else d[0] for d in self._raw.description]
        return [_Row(zip(cols, r)) for r in rows]

    @property
    def lastrowid(self) -> int | None:
        if self._is_pg:
            return self._lastrowid
        return self._raw.lastrowid


def _adapt_pg_ddl(stmt: str) -> str:
    s = stmt
    s = re.sub(
        r"id INTEGER PRIMARY KEY AUTOINCREMENT",
        "id BIGSERIAL PRIMARY KEY",
        s,
        flags=re.I,
    )
    s = re.sub(
        r"district_id INTEGER PRIMARY KEY REFERENCES",
        "district_id BIGINT PRIMARY KEY REFERENCES",
        s,
        flags=re.I,
    )
    s = s.replace("INTEGER", "BIGINT").replace("REAL", "DOUBLE PRECISION")
    return s


class CompatConnection:
    def __init__(self, raw, is_pg: bool):
        self._raw = raw
        self._is_pg = is_pg

    def execute(self, sql: str, params: tuple | list = ()):
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def executescript(self, script: str):
        return self.cursor().executescript(script)

    def executemany(self, sql: str, seq):
        return self.cursor().executemany(sql, seq)

    def cursor(self) -> CompatCursor:
        return CompatCursor(self._raw.cursor(), self._is_pg)

    def commit(self):
        self._raw.commit()

    def rollback(self):
        self._raw.rollback()


@contextmanager
def open_db(db_path: str | None = None):
    if USE_POSTGRES:
        import psycopg

        conn = psycopg.connect(DATABASE_URL, autocommit=False)
        try:
            yield CompatConnection(conn, True)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        from pathlib import Path

        path = Path(db_path or os.getenv("RELAND_DB", "data/reland.sqlite"))
        path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(str(path), timeout=15)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA busy_timeout=15000")
        try:
            yield CompatConnection(con, False)
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()


def table_has_column(c: CompatConnection, table: str, column: str) -> bool:
    if USE_POSTGRES:
        row = c.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name = %s AND column_name = %s
            """,
            (table, column),
        ).fetchone()
        return row is not None
    rows = c.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == column for r in rows)
