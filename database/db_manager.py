"""SQLite DB manager for chat accounts, avatars, and message history."""

from __future__ import annotations

import hashlib
import secrets
import sqlite3
from contextlib import closing
from os import PathLike
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_FILE_NAME = "chat_app.db"
DEFAULT_ROLE = "user"
ADMIN_ROLE = "admin"

UserRecord = Dict[str, Any]
MessageRecord = Dict[str, Any]


class DBManager:
    def __init__(self, db_name: Optional[str | PathLike] = None) -> None:
        self.db_path = Path(db_name or Path(__file__).parent / DB_FILE_NAME)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Create required tables if they do not exist."""
        with closing(self.get_connection()) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    avatar_path TEXT,
                    password_hash TEXT NOT NULL,
                    password_salt TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user'
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    msg_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id TEXT NOT NULL,
                    receiver_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    reply_to_id INTEGER,
                    action TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (reply_to_id) REFERENCES messages(msg_id)
                )
                """
            )

            conn.commit()
            self._ensure_user_table_columns(conn)

    def _ensure_user_table_columns(self, conn: sqlite3.Connection) -> None:
        existing_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()
        }

        if "password_hash" not in existing_columns:
            conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
        if "password_salt" not in existing_columns:
            conn.execute("ALTER TABLE users ADD COLUMN password_salt TEXT")
        if "role" not in existing_columns:
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
        conn.commit()

    def save_user(self, user_id: str, username: str, avatar_path: Optional[str] = None) -> None:
        with closing(self.get_connection()) as conn:
            conn.execute(
                """
                INSERT INTO users (user_id, username, avatar_path)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    avatar_path = excluded.avatar_path
                """,
                (user_id, username, avatar_path),
            )
            conn.commit()

    def get_user(self, user_id: str) -> Optional[UserRecord]:
        with closing(self.get_connection()) as conn:
            row = conn.execute(
                "SELECT user_id, username, avatar_path, role FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return dict(row) if row else None

    def get_user_by_username(self, username: str) -> Optional[UserRecord]:
        with closing(self.get_connection()) as conn:
            row = conn.execute(
                "SELECT user_id, username, avatar_path, role FROM users WHERE username = ?",
                (username,),
            ).fetchone()
        return dict(row) if row else None

    def _hash_password(self, password: str, salt: Optional[str] = None) -> tuple[str, str]:
        salt = salt or secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000,
        ).hex()
        return salt, password_hash

    def _verify_password(self, password: str, salt: str, password_hash: str) -> bool:
        _, derived_hash = self._hash_password(password, salt)
        return secrets.compare_digest(derived_hash, password_hash)

    def register_user(
        self,
        user_id: str,
        username: str,
        password: str,
        avatar_path: Optional[str] = None,
    ) -> UserRecord:
        if self.get_user_by_username(username) is not None:
            raise ValueError("Username already exists")

        salt, password_hash = self._hash_password(password)
        with closing(self.get_connection()) as conn:
            conn.execute(
                """
                INSERT INTO users (
                    user_id,
                    username,
                    avatar_path,
                    password_hash,
                    password_salt,
                    role
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, username, avatar_path, password_hash, salt, DEFAULT_ROLE),
            )
            conn.commit()

        user = self.get_user(user_id)
        if user is None:
            raise RuntimeError("Failed to load registered user")

        return user

    def authenticate_user(self, username: str, password: str) -> Optional[UserRecord]:
        with closing(self.get_connection()) as conn:
            row = conn.execute(
                """
                SELECT user_id, username, avatar_path, role, password_hash, password_salt
                FROM users
                WHERE username = ?
                """,
                (username,),
            ).fetchone()

        if not row:
            return None

        user_record = dict(row)
        if not user_record["password_hash"] or not user_record["password_salt"]:
            return None

        if self._verify_password(password, user_record["password_salt"], user_record["password_hash"]):
            user_record.pop("password_hash")
            user_record.pop("password_salt")
            return user_record

        return None

    def _has_any_admin(self) -> bool:
        with closing(self.get_connection()) as conn:
            row = conn.execute(
                "SELECT 1 FROM users WHERE role = ? LIMIT 1",
                (ADMIN_ROLE,),
            ).fetchone()
        return row is not None

    def set_user_role(self, operator_user_id: str, user_id: str, role: str) -> bool:
        if role not in {DEFAULT_ROLE, ADMIN_ROLE}:
            raise ValueError("Invalid role")

        if role == ADMIN_ROLE and not self._has_any_admin():
            if operator_user_id != user_id:
                raise PermissionError("Only admins may set user roles")
        elif not self.authorize_user(operator_user_id, [ADMIN_ROLE]):
            raise PermissionError("Only admins may set user roles")

        with closing(self.get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET role = ? WHERE user_id = ?", (role, user_id))
            conn.commit()
            return cursor.rowcount > 0

    def user_has_role(self, user_id: str, role: str) -> bool:
        user = self.get_user(user_id)
        return bool(user and user.get("role") == role)

    def authorize_user(self, user_id: str, allowed_roles: List[str]) -> bool:
        user = self.get_user(user_id)
        return bool(user and user.get("role") in allowed_roles)

    def save_message(
        self,
        sender_id: str,
        receiver_id: str,
        content: str,
        action: str = "CHAT",
        reply_to_id: Optional[int] = None,
    ) -> int:
        with closing(self.get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO messages (sender_id, receiver_id, content, action, reply_to_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (sender_id, receiver_id, content, action, reply_to_id),
            )
            msg_id = cursor.lastrowid
            if msg_id is None:
                raise RuntimeError("Không thể lấy msg_id sau khi lưu tin nhắn.")
            conn.commit()
        return msg_id

    def get_chat_history(self, user1_id: str, user2_id: str, limit: int = 50) -> List[MessageRecord]:
        with closing(self.get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT msg_id, sender_id, receiver_id, content, reply_to_id, action, timestamp
                FROM messages
                WHERE (sender_id = ? AND receiver_id = ?)
                   OR (sender_id = ? AND receiver_id = ?)
                ORDER BY timestamp ASC
                LIMIT ?
                """,
                (user1_id, user2_id, user2_id, user1_id, limit),
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def delete_message(self, msg_id: int) -> bool:
        with closing(self.get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE msg_id = ?", (msg_id,))
            conn.commit()
            deleted = cursor.rowcount > 0
        return deleted


def initialize_database(db_name: Optional[str | PathLike] = None) -> DBManager:
    return DBManager(db_name)
