# HƯỚNG DẪN TRIỂN KHAI HỆ THỐNG CHAT TCP TRÊN MẠNG LAN

## 1. Mục đích

Tài liệu hướng dẫn chạy Server và Client của hệ thống Chat TCP trên cùng một máy hoặc trên hai máy kết nối cùng mạng LAN/Wi-Fi. Ví dụ lệnh dưới đây áp dụng cho phiên bản dự án có thư mục `Code`, với chương trình Server là `Code/backend/server_main.py` và giao diện Client là `Code/client/gui_client.py`.

## 2. Chuẩn bị

- Máy chạy Server và máy chạy Client đã cài Python và các thư viện cần thiết của dự án.
- Để thử trên hai máy, hai máy cùng kết nối vào một mạng LAN/Wi-Fi và có thể liên lạc với nhau; mạng Wi-Fi không bật chế độ cách ly thiết bị.
- Chạy các lệnh tại **thư mục gốc của dự án**: thư mục chứa `Code`.
- Server sử dụng cổng TCP `5000`. Địa chỉ lắng nghe của Server là `0.0.0.0` để nhận kết nối qua các giao diện mạng của máy.

> Nếu bản code nộp dùng cổng khác, thay `5000` trong tài liệu bằng cổng thực tế. Không lấy `0.0.0.0` làm địa chỉ để Client kết nối.

## 3. Xác định địa chỉ IP của máy Server

Trên máy chạy Server, mở PowerShell hoặc Command Prompt và nhập:

```powershell
ipconfig
```

Xem mục của card mạng **đang sử dụng** (Wi-Fi hoặc Ethernet), tìm dòng **IPv4 Address**. Ví dụ địa chỉ nhận được là `192.168.20.106`. Đây chỉ là ví dụ; cần dùng địa chỉ hiện tại trên máy Server khi triển khai.

## 4. Cấu hình kết nối của Client

- **Client và Server cùng máy:** Client kết nối đến `127.0.0.1`, cổng `5000`.
- **Client trên máy khác cùng LAN/Wi-Fi:** Client kết nối đến địa chỉ IPv4 của **máy Server**, ví dụ `192.168.20.106`, cổng `5000`.

Nếu giao diện Client có ô nhập địa chỉ Server, điền địa chỉ tương ứng tại đó. Nếu địa chỉ được khai báo trong mã nguồn, tìm cấu hình `HOST` hoặc `SERVER_HOST` của **Client** và đổi thành IP Server trước khi chạy. Giữ nguyên địa chỉ Server lắng nghe `0.0.0.0` khi cần kết nối qua LAN.

## 5. Khởi động chương trình

Mở PowerShell và chuyển đến **thư mục gốc của dự án** (thư mục chứa `Code`). Thay `<duong-dan-den-du-an>` bằng đường dẫn thực tế trên máy:

```powershell
cd "<duong-dan-den-du-an>"
```

**Terminal 1 — chạy Server:**

```powershell
python Code\backend\server_main.py
```

Giữ terminal này mở. Khi Server chạy, màn hình có thể hiển thị thông báo tương tự `Server dang chay tai 0.0.0.0:5000` và `Dang cho Client ket noi...`.

**Terminal 2 — chạy Client:**

```powershell
python Code\client\gui_client.py
```

Nếu kiểm thử nhiều tài khoản trên cùng máy, mở thêm terminal và chạy lại lệnh Client. Mỗi cửa sổ Client đăng nhập bằng một tài khoản khác nhau.

Trên máy Client thứ hai, cũng mở PowerShell tại thư mục gốc của bản dự án trên máy đó rồi chạy cùng lệnh Client.

## 6. Kiểm tra kết nối

1. Khởi động Server trước, sau đó mở Client.
2. Đăng nhập hoặc đăng ký tài khoản trên Client.
3. Mở thêm một Client bằng tài khoản khác và gửi thử tin nhắn; kiểm tra tin nhắn hiển thị ở đầu nhận và log trên Server.
4. Khi Client chạy cùng máy Server, địa chỉ phía Client thường là `127.0.0.1`. Khi Client chạy trên máy khác, Server thường nhận địa chỉ IP nội bộ của máy Client.

Nếu dùng hai máy và Client không kết nối được, có thể kiểm tra cổng từ PowerShell trên **máy Client** (thay IP ví dụ bằng IP Server hiện tại):

```powershell
Test-NetConnection 192.168.20.106 -Port 5000
```

`TcpTestSucceeded : True` cho biết máy Client kết nối được tới cổng TCP của Server. Sau đó kiểm tra tiếp việc đăng nhập và gửi tin để xác nhận chức năng ứng dụng.

## 7. Xử lý lỗi thường gặp

| Hiện tượng | Cách kiểm tra |
| --- | --- |
| `can't open file` | Kiểm tra đã `cd` vào đúng thư mục chứa `Code` và tên file trong lệnh có tồn tại. |
| Client không kết nối | Kiểm tra Server đang chạy, IP của Server và cổng `5000` đã điền đúng; chạy lại `ipconfig` nếu IP thay đổi. |
| Hai máy cùng Wi-Fi nhưng không thấy nhau | Kiểm tra Wi-Fi có bật chế độ cách ly thiết bị/guest network hay không. |
| `Test-NetConnection` báo `TcpTestSucceeded : False` | Kiểm tra Server đang lắng nghe ở `0.0.0.0:5000` và Windows Defender Firewall trên máy Server có cho phép ứng dụng/cổng TCP `5000` nhận kết nối trong mạng đang dùng. |
| Kết nối được nhưng đăng nhập lỗi | Kiểm tra thông báo trên giao diện và log Server; kiểm tra cơ sở dữ liệu đã được khởi tạo theo hướng dẫn của dự án. |

## 8. Phạm vi triển khai

Hướng dẫn này dành cho hai máy **cùng LAN/Wi-Fi**. Nếu hai máy ở hai mạng Internet khác nhau, chỉ dùng IPv4 nội bộ như `192.168.x.x` là chưa đủ; cần phương án mạng riêng như VPN hoặc cấu hình mạng phù hợp để máy Client truy cập được Server.
