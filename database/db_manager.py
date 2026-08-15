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

        # Create database directory if it does not exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.init_db()

    # ============================================================
    # CONNECTION
    # ============================================================

    def get_connection(self) -> sqlite3.Connection:
        """
        Open SQLite connection and enable foreign keys.
        """
        conn = sqlite3.connect(str(self.db_path))

        # Enable SQLite foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")

        # Return rows as sqlite3.Row
        conn.row_factory = sqlite3.Row

        return conn

    # ============================================================
    # DATABASE INITIALIZATION
    # ============================================================

    def init_db(self) -> None:
        """
        Create required tables if they do not exist.
        """

        with closing(self.get_connection()) as conn:
            cursor = conn.cursor()

            # ----------------------------------------------------
            # USERS TABLE
            # ----------------------------------------------------

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

            # ----------------------------------------------------
            # MESSAGES TABLE
            # ----------------------------------------------------

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

                    FOREIGN KEY (sender_id)
                        REFERENCES users(user_id)
                        ON DELETE CASCADE,

                    FOREIGN KEY (receiver_id)
                        REFERENCES users(user_id)
                        ON DELETE CASCADE,

                    FOREIGN KEY (reply_to_id)
                        REFERENCES messages(msg_id)
                        ON DELETE SET NULL
                )
                """
            )

            conn.commit()

            # Make sure old database versions contain the
            # required users columns.
            self._ensure_user_table_columns(conn)

            conn.commit()

    # ============================================================
    # DATABASE MIGRATION
    # ============================================================

    def _ensure_user_table_columns(
        self,
        conn: sqlite3.Connection,
    ) -> None:
        """
        Ensure old databases contain the required users columns.

        This is useful when the database was created by an older
        version of the application.
        """

        existing_columns = {
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(users)"
            ).fetchall()
        }

        # Add password_hash if it does not exist.
        if "password_hash" not in existing_columns:
            conn.execute(
                """
                ALTER TABLE users
                ADD COLUMN password_hash TEXT
                """
            )

        # Add password_salt if it does not exist.
        if "password_salt" not in existing_columns:
            conn.execute(
                """
                ALTER TABLE users
                ADD COLUMN password_salt TEXT
                """
            )

        # Add role if it does not exist.
        if "role" not in existing_columns:
            conn.execute(
                """
                ALTER TABLE users
                ADD COLUMN role TEXT NOT NULL DEFAULT 'user'
                """
            )

    # ============================================================
    # USER
    # ============================================================

    def save_user(
        self,
        user_id: str,
        username: str,
        avatar_path: Optional[str] = None,
    ) -> None:
        """
        Update an existing user's basic information.

        This method is intentionally used for updating an existing
        account. New accounts should be created with register_user()
        because password_hash and password_salt are required.
        """

        existing_user = self.get_user(user_id)

        if existing_user is None:
            raise ValueError(
                "User does not exist. Use register_user() to create a new account."
            )

        with closing(self.get_connection()) as conn:
            conn.execute(
                """
                UPDATE users
                SET username = ?,
                    avatar_path = ?
                WHERE user_id = ?
                """,
                (username, avatar_path, user_id),
            )

            conn.commit()

    def get_user(
        self,
        user_id: str,
    ) -> Optional[UserRecord]:
        """
        Get user information by user_id.
        """

        with closing(self.get_connection()) as conn:
            row = conn.execute(
                """
                SELECT
                    user_id,
                    username,
                    avatar_path,
                    role
                FROM users
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()

        return dict(row) if row else None

    def get_user_by_username(
        self,
        username: str,
    ) -> Optional[UserRecord]:
        """
        Get user information by username.
        """

        with closing(self.get_connection()) as conn:
            row = conn.execute(
                """
                SELECT
                    user_id,
                    username,
                    avatar_path,
                    role
                FROM users
                WHERE username = ?
                """,
                (username,),
            ).fetchone()

        return dict(row) if row else None

    # ============================================================
    # PASSWORD HASHING
    # ============================================================

    def _hash_password(
        self,
        password: str,
        salt: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Hash password using PBKDF2-HMAC-SHA256.
        """

        salt = salt or secrets.token_hex(16)

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000,
        ).hex()

        return salt, password_hash

    def _verify_password(
        self,
        password: str,
        salt: str,
        password_hash: str,
    ) -> bool:
        """
        Verify password against stored hash.
        """

        _, derived_hash = self._hash_password(
            password,
            salt,
        )

        return secrets.compare_digest(
            derived_hash,
            password_hash,
        )

    # ============================================================
    # REGISTER
    # ============================================================

    def register_user(
        self,
        user_id: str,
        username: str,
        password: str,
        avatar_path: Optional[str] = None,
    ) -> UserRecord:
        """
        Register a new user.

        New users receive the default role 'user'.
        """

        # Check duplicate username
        if self.get_user_by_username(username) is not None:
            raise ValueError("Username already exists")

        # Check duplicate user_id
        if self.get_user(user_id) is not None:
            raise ValueError("User ID already exists")

        # Create password salt and hash
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
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    username,
                    avatar_path,
                    password_hash,
                    salt,
                    DEFAULT_ROLE,
                ),
            )

            conn.commit()

        user = self.get_user(user_id)

        if user is None:
            raise RuntimeError(
                "Failed to load registered user"
            )

        return user

    # ============================================================
    # LOGIN / AUTHENTICATION
    # ============================================================

    def authenticate_user(
        self,
        username: str,
        password: str,
    ) -> Optional[UserRecord]:
        """
        Authenticate user by username and password.

        Returns user information if successful.
        Returns None if authentication fails.
        """

        with closing(self.get_connection()) as conn:
            row = conn.execute(
                """
                SELECT
                    user_id,
                    username,
                    avatar_path,
                    role,
                    password_hash,
                    password_salt
                FROM users
                WHERE username = ?
                """,
                (username,),
            ).fetchone()

        if not row:
            return None

        user_record = dict(row)

        password_hash = user_record.get("password_hash")
        password_salt = user_record.get("password_salt")

        # Old/incomplete account
        if not password_hash or not password_salt:
            return None

        # Verify password
        if self._verify_password(
            password,
            password_salt,
            password_hash,
        ):
            # Never return password information
            user_record.pop("password_hash", None)
            user_record.pop("password_salt", None)

            return user_record

        return None

    # ============================================================
    # ROLE / PERMISSION
    # ============================================================

    def _has_any_admin(self) -> bool:
        """
        Check whether at least one admin exists.
        """

        with closing(self.get_connection()) as conn:
            row = conn.execute(
                """
                SELECT 1
                FROM users
                WHERE role = ?
                LIMIT 1
                """,
                (ADMIN_ROLE,),
            ).fetchone()

        return row is not None

    def set_user_role(
        self,
        operator_user_id: str,
        user_id: str,
        role: str,
    ) -> bool:
        """
        Change user's role.

        Allowed roles:
            - user
            - admin

        The first admin can be created by setting their own role
        when no admin exists yet.
        """

        if role not in {
            DEFAULT_ROLE,
            ADMIN_ROLE,
        }:
            raise ValueError("Invalid role")

        # First admin setup
        if role == ADMIN_ROLE and not self._has_any_admin():
            if operator_user_id != user_id:
                raise PermissionError(
                    "Only admins may set user roles"
                )

        # Normal role changes require admin permission
        elif not self.authorize_user(
            operator_user_id,
            [ADMIN_ROLE],
        ):
            raise PermissionError(
                "Only admins may set user roles"
            )

        with closing(self.get_connection()) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE users
                SET role = ?
                WHERE user_id = ?
                """,
                (role, user_id),
            )

            conn.commit()

            return cursor.rowcount > 0

    def user_has_role(
        self,
        user_id: str,
        role: str,
    ) -> bool:
        """
        Check whether a user has a specific role.
        """

        user = self.get_user(user_id)

        return bool(
            user
            and user.get("role") == role
        )

    def authorize_user(
        self,
        user_id: str,
        allowed_roles: List[str],
    ) -> bool:
        """
        Check whether user has one of the allowed roles.
        """

        user = self.get_user(user_id)

        return bool(
            user
            and user.get("role") in allowed_roles
        )

    # ============================================================
    # MESSAGES
    # ============================================================

    def save_message(
        self,
        sender_id: str,
        receiver_id: str,
        content: str,
        action: str = "CHAT",
        reply_to_id: Optional[int] = None,
    ) -> int:
        """
        Save a chat message.

        sender_id and receiver_id must exist in users.
        reply_to_id must reference an existing message if provided.
        """

        with closing(self.get_connection()) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO messages (
                    sender_id,
                    receiver_id,
                    content,
                    action,
                    reply_to_id
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    sender_id,
                    receiver_id,
                    content,
                    action,
                    reply_to_id,
                ),
            )

            msg_id = cursor.lastrowid

            if msg_id is None:
                raise RuntimeError(
                    "Không thể lấy msg_id sau khi lưu tin nhắn."
                )

            conn.commit()

        return int(msg_id)

    # ============================================================
    # CHAT HISTORY
    # ============================================================

    def get_chat_history(
        self,
        user1_id: str,
        user2_id: str,
        limit: int = 50,
    ) -> List[MessageRecord]:
        """
        Get chat history between two users.
        """

        if limit <= 0:
            return []

        with closing(self.get_connection()) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    msg_id,
                    sender_id,
                    receiver_id,
                    content,
                    reply_to_id,
                    action,
                    timestamp
                FROM messages
                WHERE
                    (sender_id = ? AND receiver_id = ?)
                    OR
                    (sender_id = ? AND receiver_id = ?)
                ORDER BY timestamp ASC
                LIMIT ?
                """,
                (
                    user1_id,
                    user2_id,
                    user2_id,
                    user1_id,
                    limit,
                ),
            )

            rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    # ============================================================
    # DELETE MESSAGE
    # ============================================================

    def delete_message(
        self,
        msg_id: int,
    ) -> bool:
        """
        Delete a message.

        Messages replying to this message will automatically have
        reply_to_id set to NULL because of ON DELETE SET NULL.
        """

        with closing(self.get_connection()) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                DELETE FROM messages
                WHERE msg_id = ?
                """,
                (msg_id,),
            )

            conn.commit()

            deleted = cursor.rowcount > 0

        return deleted


# ================================================================
# DATABASE INITIALIZER
# ================================================================

def initialize_database(
    db_name: Optional[str | PathLike] = None,
) -> DBManager:
    """
    Create and initialize DBManager.
    """

    return DBManager(db_name)