"""
Migration: them cot 'gender' va 'birthday' vao bang users cua chat.db
DA TON TAI (khong xoa du lieu cu). Chi can chay 1 lan.

Cach chay (tu thu muc goc UDM08_CHAT_PYTHON):
    python -m Code.database.migrate_add_profile_fields
hoac:
    python Code/database/migrate_add_profile_fields.py

An toan chay lai nhieu lan: neu cot da ton tai thi bo qua, khong loi.
"""

import sqlite3
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from Code.config.db_config import DB_PATH


def _existing_columns(cur: sqlite3.Cursor, table: str) -> set[str]:
    cur.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cur.fetchall()}


def migrate() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        columns = _existing_columns(cur, "users")

        if "gender" not in columns:
            cur.execute(
                "ALTER TABLE users ADD COLUMN gender TEXT DEFAULT NULL "
                "CHECK (gender IN ('male', 'female', 'other') OR gender IS NULL)"
            )
            print("[OK] Da them cot 'gender' vao bang users.")
        else:
            print("[SKIP] Cot 'gender' da ton tai.")

        if "birthday" not in columns:
            cur.execute("ALTER TABLE users ADD COLUMN birthday TEXT DEFAULT NULL")
            print("[OK] Da them cot 'birthday' vao bang users.")
        else:
            print("[SKIP] Cot 'birthday' da ton tai.")

        conn.commit()
    finally:
        conn.close()

    print(f"Migration hoan tat tren: {DB_PATH}")


if __name__ == "__main__":
    migrate()