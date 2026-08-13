SERVER CORE - UDM08

Chi sua phan server. Khong sua client/database/shared/tests/tools.

Protocol khop Client GUI hien tai:
LOGIN|username
MESSAGE|content
PRIVATE|receiver|content
PING
LOGOUT

Server tra:
SYSTEM|...
ONLINE|user1,user2
MESSAGE|sender|content
PRIVATE|sender|content
PONG
ERROR|...

Cach thay vao project:
1. Sao luu thu muc server cu.
2. Copy cac file trong thu muc nay vao <project>/server/.
3. Tu thu muc goc project chay:
   python -m server.server
   hoac python server/server.py
4. Mo client bang:
   python client/chat_window.py
