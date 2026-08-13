import socket

HOST = "127.0.0.1"
PORT = 5000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    client.connect((HOST, PORT))
    print(client.recv(4096).decode("utf-8").strip())

    while True:
        message = input("Nhap tin nhan: ").strip()

        if message.lower() == "exit":
            client.sendall("LOGOUT\n".encode("utf-8"))
            break

        client.sendall(f"MESSAGE|{message}\n".encode("utf-8"))
        print(client.recv(4096).decode("utf-8").strip())
