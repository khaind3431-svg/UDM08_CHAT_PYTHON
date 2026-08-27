"""
profile_service.py - Lay thong tin ca nhan cua 1 user de hien thi cho
nguoi khac xem (ho ten, bio, trang thai online, quan he ket ban).
"""

from Code.backend.core.db_connection import db_cursor
from Code.backend.services.contact_service import get_friend_status


def get_user_profile(viewer_username: str, viewer_id: int, target_username: str) -> dict:
    target_username = target_username.strip()
    if not target_username:
        return {"ok": False, "error": "Ten dang nhap khong hop le."}

    with db_cursor() as cur:
        cur.execute(
            """SELECT id, username, full_name, bio, status, last_seen_at
               FROM users WHERE username = ?""",
            (target_username,),
        )
        row = cur.fetchone()

    if row is None:
        return {"ok": False, "error": f"Nguoi dung {target_username} khong ton tai."}

    if target_username == viewer_username:
        friend_status = "self"
    else:
        friend_status = get_friend_status(viewer_id, row["id"])

    return {
        "ok": True,
        "profile": {
            "username": row["username"],
            "full_name": row["full_name"] or row["username"],
            "bio": row["bio"] or "",
            "status": row["status"] or "offline",
            "friend_status": friend_status,
        },
    }