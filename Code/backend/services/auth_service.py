from Code.backend.core.db_connection import db_cursor
from Code.backend.utils.hash_utils import hash_password, verify_password


def register_user(display_name: str, username: str, password: str, confirm_password: str) -> dict:
    if not display_name or not username or not password:
        return {"ok": False, "error": "Vui long nhap day du thong tin."}
    if password != confirm_password:
        return {"ok": False, "error": "Mat khau nhap lai khong khop."}
    if len(password) < 6:
        return {"ok": False, "error": "Mat khau phai tu 6 ky tu."}

    with db_cursor() as cur:
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cur.fetchone():
            return {"ok": False, "error": "Ten dang nhap da ton tai."}

        cur.execute(
            """INSERT INTO users (username, password_hash, full_name, status)
               VALUES (?, ?, ?, 'offline')""",
            (username, hash_password(password), display_name),
        )
    return {"ok": True}


def authenticate_user(username: str, password: str) -> dict:
    with db_cursor() as cur:
        cur.execute(
            "SELECT id, username, password_hash, full_name, is_active "
            "FROM users WHERE username = ?",
            (username,),
        )
        row = cur.fetchone()

    if row is None:
        return {"ok": False, "error": "Tai khoan khong ton tai."}
    if not row["is_active"]:
        return {"ok": False, "error": "Tai khoan da bi khoa."}
    if not verify_password(password, row["password_hash"]):
        return {"ok": False, "error": "Sai mat khau."}

    return {
        "ok": True,
        "user": {
            "id": row["id"],
            "username": row["username"],
            "full_name": row["full_name"],
        },
    }


def set_user_status(user_id: int, status: str) -> None:
    with db_cursor() as cur:
        cur.execute(
            "UPDATE users SET status = ?, last_seen_at = datetime('now') WHERE id = ?",
            (status, user_id),
        )