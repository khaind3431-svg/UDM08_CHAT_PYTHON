"""
profile_service.py - Lay thong tin ca nhan cua 1 user de hien thi cho
nguoi khac xem (ho ten, bio, gioi tinh, ngay sinh, avatar, trang thai
online, quan he ket ban), va cap nhat ho so cua chinh minh.
"""

from Code.backend.core.db_connection import db_cursor
from Code.backend.services.contact_service import get_friend_status
from Code.backend.utils import validators


def get_user_profile(viewer_username: str, viewer_id: int, target_username: str) -> dict:
    target_username = target_username.strip()
    if not target_username:
        return {"ok": False, "error": "Ten dang nhap khong hop le."}

    with db_cursor() as cur:
        cur.execute(
            """SELECT id, username, full_name, bio, gender, birthday,
                      avatar_url, status, last_seen_at
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
            "gender": row["gender"] or "",
            "birthday": row["birthday"] or "",
            "avatar_url": row["avatar_url"] or "",
            "status": row["status"] or "offline",
            "friend_status": friend_status,
        },
    }


def update_profile(user_id: int, full_name: str, bio: str, gender: str, birthday: str) -> dict:
    """Cap nhat ten hien thi / bio / gioi tinh / ngay sinh cua CHINH
    user_id. Khong dung ham nay de sua thong tin nguoi khac."""
    full_name = (full_name or "").strip()
    bio = (bio or "").strip()
    gender = (gender or "").strip().lower()
    birthday = (birthday or "").strip()

    error = (
        validators.validate_full_name(full_name)
        or validators.validate_bio(bio)
        or validators.validate_gender(gender)
        or validators.validate_birthday(birthday)
    )
    if error:
        return {"ok": False, "error": error}

    with db_cursor() as cur:
        cur.execute(
            """UPDATE users
               SET full_name = ?, bio = ?, gender = ?, birthday = ?
               WHERE id = ?""",
            (full_name, bio or None, gender or None, birthday or None, user_id),
        )

    return {"ok": True}


def update_avatar(user_id: int, avatar_data_uri: str) -> dict:
    """Cap nhat anh dai dien cua CHINH user_id. avatar_data_uri la chuoi
    dang 'data:<mime>;base64,<data>' da duoc validate o media_service."""
    with db_cursor() as cur:
        cur.execute(
            "UPDATE users SET avatar_url = ? WHERE id = ?",
            (avatar_data_uri, user_id),
        )
    return {"ok": True}