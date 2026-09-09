"""
contact_service.py - Nghiep vu ket ban: gui loi moi, phan hoi loi moi,
lay danh sach ban be va danh sach loi moi dang cho.
"""

from Code.backend.core.db_connection import db_cursor


def _get_user_id(cur, username: str):
    cur.execute("SELECT id FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    return row["id"] if row else None


def _resolve_target_user(cur, query: str):
    cur.execute("SELECT id, username FROM users WHERE username = ?", (query,))
    row = cur.fetchone()
    if row:
        return row["id"], row["username"], None

    cur.execute("SELECT id, username FROM users WHERE full_name = ? COLLATE NOCASE", (query,))
    rows = cur.fetchall()
    if len(rows) == 1:
        return rows[0]["id"], rows[0]["username"], None
    if len(rows) > 1:
        return None, None, "ambiguous"
    return None, None, None


def send_friend_request(from_username: str, to_query: str) -> dict:
    with db_cursor() as cur:
        from_id = _get_user_id(cur, from_username)
        to_id, to_username, resolve_error = _resolve_target_user(cur, to_query)

        if resolve_error == "ambiguous":
            return {
                "ok": False,
                "error": f"Co nhieu nguoi dung ten hien thi '{to_query}'. "
                         f"Vui long nhap dung ten dang nhap (username) de ket ban chinh xac.",
            }
        if from_id is None or to_id is None:
            return {"ok": False, "error": f"Nguoi dung {to_query} khong ton tai."}
        if from_id == to_id:
            return {"ok": False, "error": "Ban khong the tu ket ban voi chinh minh."}

        cur.execute(
            """SELECT id, user_id, contact_id, status FROM contacts
               WHERE (user_id = ? AND contact_id = ?)
                  OR (user_id = ? AND contact_id = ?)""",
            (from_id, to_id, to_id, from_id),
        )
        existing = cur.fetchone()

        if existing is None:
            cur.execute(
                "INSERT INTO contacts (user_id, contact_id, status) VALUES (?, ?, 'pending')",
                (from_id, to_id),
            )
            return {"ok": True}

        if existing["status"] == "accepted":
            return {"ok": False, "error": "Hai nguoi da la ban be."}

        if existing["status"] == "pending":
            if existing["user_id"] == from_id:
                return {"ok": False, "error": "Loi moi ket ban da duoc gui truoc do."}
            return {
                "ok": False,
                "error": f"{to_username} da gui loi moi ket ban cho ban. "
                         f"Hay vao muc loi moi de phan hoi.",
            }

        if existing["status"] == "blocked":
            return {"ok": False, "error": "Khong the gui loi moi ket ban."}

        cur.execute(
            "UPDATE contacts SET user_id = ?, contact_id = ?, status = 'pending' WHERE id = ?",
            (from_id, to_id, existing["id"]),
        )
        return {"ok": True}


def respond_friend_request(responder_username: str, requester_username: str,
                            accept: bool) -> dict:
    with db_cursor() as cur:
        responder_id = _get_user_id(cur, responder_username)
        requester_id = _get_user_id(cur, requester_username)

        if responder_id is None or requester_id is None:
            return {"ok": False, "error": "Nguoi dung khong ton tai."}

        cur.execute(
            """SELECT id FROM contacts
               WHERE user_id = ? AND contact_id = ? AND status = 'pending'""",
            (requester_id, responder_id),
        )
        row = cur.fetchone()
        if row is None:
            return {"ok": False, "error": "Khong tim thay loi moi ket ban nay."}

        new_status = "accepted" if accept else "rejected"
        cur.execute(
            "UPDATE contacts SET status = ? WHERE id = ?",
            (new_status, row["id"]),
        )
        return {"ok": True}


def get_friend_list(username: str) -> list:
    with db_cursor() as cur:
        my_id = _get_user_id(cur, username)
        if my_id is None:
            return []

        cur.execute(
            """SELECT u.username FROM contacts c
               JOIN users u
                 ON u.id = CASE WHEN c.user_id = ? THEN c.contact_id ELSE c.user_id END
               WHERE c.status = 'accepted' AND (c.user_id = ? OR c.contact_id = ?)""",
            (my_id, my_id, my_id),
        )
        return [row["username"] for row in cur.fetchall()]

def get_friend_status(viewer_id: int, target_id: int) -> str:
    """Tra ve quan he ket ban giua 2 user (theo id), dung cho GETINFO."""
    if viewer_id == target_id:
        return "self"

    with db_cursor() as cur:
        cur.execute(
            """SELECT user_id, contact_id, status FROM contacts
               WHERE (user_id = ? AND contact_id = ?)
                  OR (user_id = ? AND contact_id = ?)""",
            (viewer_id, target_id, target_id, viewer_id),
        )
        row = cur.fetchone()

    if row is None:
        return "none"
    if row["status"] == "accepted":
        return "friends"
    if row["status"] == "pending":
        return "pending_sent" if row["user_id"] == viewer_id else "pending_received"
    return "none"
def get_friend_requests(username: str) -> list:
    with db_cursor() as cur:
        my_id = _get_user_id(cur, username)
        if my_id is None:
            return []

        cur.execute(
            """SELECT u.username FROM contacts c
               JOIN users u ON u.id = c.user_id
               WHERE c.contact_id = ? AND c.status = 'pending'""",
            (my_id,),
        )
        return [row["username"] for row in cur.fetchall()]