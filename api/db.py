import os
import sqlite3
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{_PROJECT_ROOT}/db/coupledmd.sqlite")


def get_connection() -> sqlite3.Connection:
    if not _DATABASE_URL.startswith("sqlite:///"):
        raise RuntimeError(
            f"Only SQLite supported currently. Set DATABASE_URL=sqlite:///path. Got: {_DATABASE_URL}"
        )
    db_path = Path(_DATABASE_URL.replace("sqlite:///", ""))
    if not db_path.is_absolute():
        db_path = _PROJECT_ROOT / db_path
    con = sqlite3.connect(db_path, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con
