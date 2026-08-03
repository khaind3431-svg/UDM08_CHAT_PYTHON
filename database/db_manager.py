"""SQLite DB manager for chat accounts, avatars, and message history."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_FILE_NAME = "chat_app.db"

UserRecord = Dict[str, Any]
MessageRecord = Dict[str, Any]


class DBManager:
    def __init__(self, db_name: Optional[str] = None) -> None:
        self.db_path = Path(db_name or Path(__file__).parent / DB_FILE_NAME)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Create required tables if they do not exist."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                avatar_path TEXT
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
        conn.close()

    def save_user(self, user_id: str, username: str, avatar_path: Optional[str] = None) -> None:
        with self.get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO users (user_id, username, avatar_path) VALUES (?, ?, ?)",
                (user_id, username, avatar_path),
            )

    def get_user(self, user_id: str) -> Optional[UserRecord]:
        conn = self.get_connection()
        row = conn.execute(
            "SELECT user_id, username, avatar_path FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def save_message(
        self,
        sender_id: str,
        receiver_id: str,
        content: str,
        action: str = "CHAT",
        reply_to_id: Optional[int] = None,
    ) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO messages (sender_id, receiver_id, content, action, reply_to_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sender_id, receiver_id, content, action, reply_to_id),
        )
        msg_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return msg_id

    def get_chat_history(self, user1_id: str, user2_id: str, limit: int = 50) -> List[MessageRecord]:
        conn = self.get_connection()
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
        conn.close()
        return [dict(row) for row in rows]

    def delete_message(self, msg_id: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE msg_id = ?", (msg_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted


def initialize_database(db_name: Optional[str] = None) -> DBManager:
    return DBManager(db_name)
