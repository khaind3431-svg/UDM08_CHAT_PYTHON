from database.db_manager import DBManager
from shared.protocol import Protocol

# Test DB
print("=== DB Test ===")
db = DBManager("test_chat.db")
msg_id = db.save_message("user_A", "user_B", "Chào bạn! 😊")
print(f"Đã lưu tin nhắn ID: {msg_id}")

history = db.get_chat_history("user_A", "user_B")
print("Lịch sử chat:")
for row in history:
    print(row)


# Test Protocol
print("\n=== Protocol Test ===")
packet = Protocol.create_chat_message("user_A", "user_B", "Chào bạn! 😊")
print("Gói tin JSON:", packet)

encoded = packet if isinstance(packet, str) else str(packet)
print("Kích thước payload:", len(encoded))
