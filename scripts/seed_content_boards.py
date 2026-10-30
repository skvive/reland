#!/usr/bin/env python3
"""Apply v3.0.2 editorial content to community boards (local or Neon)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from app import db, init_db, utcnow  # noqa: E402
from content_publisher import apply_published_content  # noqa: E402
from db_engine import table_has_column  # noqa: E402


def main() -> None:
    force = "--force" in sys.argv
    init_db()
    with db() as c:
        result = apply_published_content(c, utcnow, table_has_column, force=force)
    print(result)


if __name__ == "__main__":
    main()
