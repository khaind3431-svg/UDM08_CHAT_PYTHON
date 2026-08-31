"""Kiem tra va luu anh do client gui qua giao thuc TCP."""

import base64
import binascii
import re
import uuid
from pathlib import Path


MAX_IMAGE_BYTES = 2 * 1024 * 1024
# Avatar duoc gui kem trong MOI lan xem ho so (USERINFO), nen gioi han
# nho hon nhieu so voi anh chat thuong de tranh lam nang giao thuc.
MAX_AVATAR_BYTES = 300 * 1024
ALLOWED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"


class MediaError(ValueError):
    pass


def save_image(file_name: str, mime_type: str, data_base64: str) -> dict:
    mime_type = mime_type.strip().lower()
    if mime_type not in ALLOWED_MIME_TYPES:
        raise MediaError("Chi chap nhan anh JPG, PNG, GIF hoac WEBP.")

    try:
        raw = base64.b64decode(data_base64, validate=True)
    except (binascii.Error, ValueError):
        raise MediaError("Du lieu anh khong hop le.")

    if not raw:
        raise MediaError("Anh rong.")
    if len(raw) > MAX_IMAGE_BYTES:
        raise MediaError("Anh vuot qua gioi han 2 MB.")

    safe_stem = Path(file_name or "image").stem
    safe_stem = re.sub(r"[^A-Za-z0-9_-]+", "_", safe_stem).strip("_") or "image"
    stored_name = f"{safe_stem}_{uuid.uuid4().hex[:12]}{ALLOWED_MIME_TYPES[mime_type]}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / stored_name).write_bytes(raw)

    return {
        "file_name": Path(file_name or stored_name).name.replace("|", "_"),
        "stored_name": stored_name,
        "mime_type": mime_type,
        "size": len(raw),
    }


def validate_avatar(mime_type: str, data_base64: str) -> tuple[bytes, str]:
    """Kiem tra dinh dang/kich thuoc anh dai dien. Khong ghi file ra dia
    vi anh dai dien duoc luu thang duoi dang data-URI trong cot
    users.avatar_url (xem profile_service.update_avatar)."""
    mime_type = mime_type.strip().lower()
    if mime_type not in ALLOWED_MIME_TYPES:
        raise MediaError("Chi chap nhan anh JPG, PNG, GIF hoac WEBP.")

    try:
        raw = base64.b64decode(data_base64, validate=True)
    except (binascii.Error, ValueError):
        raise MediaError("Du lieu anh khong hop le.")

    if not raw:
        raise MediaError("Anh rong.")
    if len(raw) > MAX_AVATAR_BYTES:
        raise MediaError("Anh dai dien vuot qua gioi han 300 KB.")

    return raw, mime_type