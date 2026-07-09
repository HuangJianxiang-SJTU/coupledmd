"""
Optional user accounts for CoupledMD.

Accounts are CONVENIENCE ONLY — they provide:
  - Saved queries / sessions
  - A Tier-1 API key (higher rate limit)
  - Opt-in update notifications

No data, download, or analysis is ever account-gated.
Passwords are hashed with argon2id.  Self-service deletion and data export.
"""

import os
import secrets
import sqlite3
import time
from pathlib import Path

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from .rate_limit import issue_key, delete_key

_ACCOUNTS_DB = Path(
    os.environ.get(
        "ACCOUNTS_DB_PATH",
        os.path.join(os.environ.get("DATA_ROOT", str(Path(__file__).resolve().parent.parent)),
                     "data", "accounts.db"),
    )
)

_ph = PasswordHasher()


def _get_conn() -> sqlite3.Connection:
    _ACCOUNTS_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_ACCOUNTS_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create the accounts table if it doesn't exist."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            email         TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name          TEXT DEFAULT '',
            institution   TEXT DEFAULT '',
            research_area TEXT DEFAULT '',
            api_key       TEXT,
            notify_updates INTEGER DEFAULT 0,
            created_at    REAL NOT NULL,
            last_login    REAL
        )
    """)
    conn.commit()
    conn.close()


# Eagerly create the accounts table at import time, mirroring the keys-DB
# eager init in rate_limit.py, so the table always exists before the first
# account request regardless of when the lifespan handler runs.
init_db()


def create_account(email: str, password: str, name: str = "",
                   institution: str = "", research_area: str = "",
                   notify_updates: bool = False) -> dict:
    """Create an account and return its data (minus password hash)."""
    init_db()
    pw_hash = _ph.hash(password)
    api_key = issue_key(email=email, institution=institution, name=name)
    now = time.time()

    conn = _get_conn()
    try:
        conn.execute(
            """INSERT INTO accounts
               (email, password_hash, name, institution, research_area, api_key, notify_updates, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (email, pw_hash, name, institution, research_area, api_key,
             1 if notify_updates else 0, now),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError("Email already registered")
    conn.close()

    return {
        "email": email,
        "name": name,
        "institution": institution,
        "api_key": api_key,
    }


def verify_account(email: str, password: str) -> dict | None:
    """Verify credentials. Returns account dict (minus hash) or None."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM accounts WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        return None
    try:
        _ph.verify(row["password_hash"], password)
    except VerifyMismatchError:
        return None
    # Update last_login
    conn = _get_conn()
    conn.execute("UPDATE accounts SET last_login = ? WHERE id = ?", (time.time(), row["id"]))
    conn.commit()
    conn.close()
    return {k: v for k, v in dict(row).items() if k != "password_hash"}


def get_account(email: str) -> dict | None:
    """Get account by email (minus password hash)."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM accounts WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        return None
    return {k: v for k, v in dict(row).items() if k != "password_hash"}


def delete_account(email: str) -> bool:
    """Delete an account and its API key. Returns True if it existed."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT api_key FROM accounts WHERE email = ?", (email,))
    row = cur.fetchone()
    if row is None:
        conn.close()
        return False
    if row["api_key"]:
        delete_key(row["api_key"])
    cur.execute("DELETE FROM accounts WHERE email = ?", (email,))
    conn.commit()
    conn.close()
    return True


def export_account_data(email: str) -> dict | None:
    """Export all stored data for an account (GDPR/PIPL data portability)."""
    account = get_account(email)
    if account is None:
        return None
    return {
        "account": account,
        "exported_at": time.time(),
        "notice": "This is all data CoupledMD stores about your account.",
    }


def update_account(email: str, **fields) -> dict | None:
    """Update account fields. Allowed: name, institution, research_area, notify_updates."""
    allowed = {"name", "institution", "research_area", "notify_updates"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return get_account(email)
    conn = _get_conn()
    sets = ", ".join(f"{k} = ?" for k in updates)
    conn.execute(f"UPDATE accounts SET {sets} WHERE email = ?",
                 list(updates.values()) + [email])
    conn.commit()
    conn.close()
    return get_account(email)
