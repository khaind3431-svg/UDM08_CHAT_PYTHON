"""
validators.py - Kiem tra hop le du lieu ho so ca nhan nguoi dung
(ten hien thi, bio, gioi tinh, ngay sinh) truoc khi luu vao DB.

Moi ham tra ve None neu hop le, hoac 1 chuoi thong bao loi (tieng Viet)
neu khong hop le.
"""

import re
from datetime import date
from typing import Optional

VALID_GENDERS = {"male", "female", "other", ""}

_BIRTHDAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_full_name(value: str) -> Optional[str]:
    value = (value or "").strip()
    if not value:
        return "Ten hien thi khong duoc de trong."
    if len(value) > 100:
        return "Ten hien thi toi da 100 ky tu."
    return None


def validate_bio(value: str) -> Optional[str]:
    if value and len(value) > 300:
        return "Tieu su toi da 300 ky tu."
    return None


def validate_gender(value: str) -> Optional[str]:
    if value not in VALID_GENDERS:
        return "Gioi tinh khong hop le."
    return None


def validate_birthday(value: str) -> Optional[str]:
    """value rong ('') nghia la khong dat ngay sinh -> hop le."""
    if not value:
        return None

    if not _BIRTHDAY_RE.match(value):
        return "Ngay sinh khong hop le (dung dinh dang YYYY-MM-DD)."

    year, month, day = (int(part) for part in value.split("-"))
    try:
        birthday = date(year, month, day)
    except ValueError:
        return "Ngay sinh khong hop le."

    if birthday > date.today():
        return "Ngay sinh khong duoc o tuong lai."
    if year < 1900:
        return "Nam sinh khong hop le."

    return None