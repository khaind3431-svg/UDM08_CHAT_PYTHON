import os
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database.db_manager import DBManager


class DBManagerTest(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmpdir.name) / "test_chat.db"
        self.db = DBManager(self.db_path)

    def tearDown(self):
        self.tmpdir.cleanup()

    # 1. Kiểm tra bảng users được tạo
    def test_users_table_is_created(self):
        conn = sqlite3.connect(str(self.db_path))

        row = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='users'"
        ).fetchone()

        conn.close()

        self.assertIsNotNone(row)

    # 2. Kiểm tra đăng ký tài khoản
    def test_register_user(self):
        user = self.db.register_user(
            "user001",
            "tai",
            "123456"
        )

        self.assertEqual(user["user_id"], "user001")
        self.assertEqual(user["username"], "tai")
        self.assertEqual(user["role"], "user")

    # 3. Không cho đăng ký username trùng
    def test_duplicate_username(self):
        self.db.register_user(
            "user001",
            "tai",
            "123456"
        )

        with self.assertRaises(ValueError):
            self.db.register_user(
                "user002",
                "tai",
                "654321"
            )

    # 4. Đăng nhập đúng mật khẩu
    def test_login_success(self):
        self.db.register_user(
            "user001",
            "tai",
            "123456"
        )

        user = self.db.authenticate_user(
            "tai",
            "123456"
        )

        self.assertIsNotNone(user)

        if user is not None:
            self.assertEqual(user["username"], "tai")
            self.assertEqual(user["role"], "user")

    # 5. Đăng nhập sai mật khẩu
    def test_login_wrong_password(self):
        self.db.register_user(
            "user001",
            "tai",
            "123456"
        )

        user = self.db.authenticate_user(
            "tai",
            "wrongpassword"
        )

        self.assertIsNone(user)

    # 6. Tài khoản đăng ký mặc định là user
    def test_default_role(self):
        self.db.register_user(
            "user001",
            "tai",
            "123456"
        )

        self.assertTrue(
            self.db.user_has_role(
                "user001",
                "user"
            )
        )

    # 7. Kiểm tra quyền admin
    def test_admin_role(self):
        self.db.register_user(
            "admin001",
            "admin",
            "admin123"
        )

        # Tạo admin ban đầu cho mục đích kiểm thử
        with closing(self.db.get_connection()) as conn:
            conn.execute(
                "UPDATE users SET role = 'admin' WHERE user_id = ?",
                ("admin001",)
            )
            conn.commit()

        self.assertTrue(
            self.db.user_has_role(
                "admin001",
                "admin"
            )
        )

    # 8. Admin có thể cấp quyền cho user
    def test_admin_change_user_role(self):
        # Tạo tài khoản admin
        self.db.register_user(
            "admin001",
            "admin",
            "admin123"
        )

        # Tạo tài khoản user
        self.db.register_user(
            "user001",
            "tai",
            "123456"
        )

        # Thiết lập admin ban đầu cho mục đích kiểm thử
        with closing(self.db.get_connection()) as conn:
            conn.execute(
                "UPDATE users SET role = 'admin' WHERE user_id = ?",
                ("admin001",)
            )
            conn.commit()

        # Admin cấp quyền admin cho user
        result = self.db.set_user_role(
            "admin001",
            "user001",
            "admin"
        )

        self.assertTrue(result)

        # Kiểm tra user đã trở thành admin
        self.assertTrue(
            self.db.user_has_role(
                "user001",
                "admin"
            )
        )


if __name__ == "__main__":
    unittest.main()