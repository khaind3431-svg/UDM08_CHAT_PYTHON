import socket
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

HOST = "127.0.0.1"
PORT = 5000

BUFFER_SIZE = 4096
ENCODING = "utf-8"


class ChatWindow:

    def __init__(self):

        self.client = None

        self.window = tk.Tk()
        self.window.title("TCP Chat")
        self.window.geometry("900x600")

        self.username = ""

        self.create_login()

        self.window.mainloop()

    # ==================================
    # LOGIN
    # ==================================

    def create_login(self):

        login_frame = tk.Frame(self.window)
        login_frame.pack(pady=30)

        tk.Label(
            login_frame,
            text="Username",
            font=("Arial", 12)
        ).pack()

        self.username_entry = tk.Entry(
            login_frame,
            width=25,
            font=("Arial", 12)
        )

        self.username_entry.pack(pady=10)

        ttk.Button(
            login_frame,
            text="Connect",
            command=self.connect_server
        ).pack()

        self.login_frame = login_frame

    # ==================================
    # CONNECT
    # ==================================

    def connect_server(self):

        username = self.username_entry.get().strip()

        if username == "":
            messagebox.showerror(
                "Error",
                "Nhap username."
            )
            return

        self.username = username

        try:

            self.client = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )

            self.client.connect((HOST, PORT))

            self.client.sendall(
                f"LOGIN|{username}\n".encode(ENCODING)
            )

        except Exception as e:

            messagebox.showerror(
                "Error",
                str(e)
            )

            return

        self.login_frame.destroy()

        self.create_chat_ui()

        threading.Thread(
            target=self.receive,
            daemon=True
        ).start()

    # ==================================
    # CHAT UI
    # ==================================

    def create_chat_ui(self):

        left = tk.Frame(self.window)
        left.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
        )

        right = tk.Frame(self.window, width=180)
        right.pack(
            side=tk.RIGHT,
            fill=tk.Y
        )

        self.chat_box = ScrolledText(
            left,
            state="disabled",
            font=("Arial", 11)
        )

        self.chat_box.pack(
            fill=tk.BOTH,
            expand=True,
            padx=5,
            pady=5
        )

        bottom = tk.Frame(left)
        bottom.pack(fill=tk.X)

        self.message_entry = tk.Entry(
            bottom,
            font=("Arial", 12)
        )

        self.message_entry.pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True,
            padx=5,
            pady=5
        )

        self.message_entry.bind(
            "<Return>",
            self.send_message
        )

        ttk.Button(
            bottom,
            text="Send",
            command=self.send_message
        ).pack(
            side=tk.RIGHT,
            padx=5
        )

        ttk.Button(
            bottom,
            text="Clear",
            command=self.clear_chat
        ).pack(
            side=tk.RIGHT
        )

        tk.Label(
            right,
            text="Online",
            font=("Arial", 13, "bold")
        ).pack(pady=5)

        self.online_list = tk.Listbox(
            right,
            font=("Arial", 11)
        )

        self.online_list.pack(
            fill=tk.BOTH,
            expand=True,
            padx=5,
            pady=5
        )

    # ==================================
    # SEND
    # ==================================

    def send_message(self, event=None):

        msg = self.message_entry.get().strip()

        if msg == "":
            return

        packet = f"MESSAGE|{msg}\n"

        try:

            self.client.sendall(
                packet.encode(ENCODING)
            )

        except:

            messagebox.showerror(
                "Error",
                "Mat ket noi Server."
            )

        self.message_entry.delete(
            0,
            tk.END
        )

    # ==================================
    # RECEIVE
    # ==================================

    def receive(self):

        while True:

            try:

                data = self.client.recv(
                    BUFFER_SIZE
                )

                if not data:
                    break

                messages = data.decode(
                    ENCODING
                ).split("\n")

                for msg in messages:

                    if msg != "":
                        self.process_message(msg)

            except:
                break

    # ==================================
    # PROCESS
    # ==================================

    def process_message(self, message):

        parts = message.split("|")

        if parts[0] == "ONLINE":

            self.online_list.delete(
                0,
                tk.END
            )

            if len(parts) > 1:

                users = parts[1].split(",")

                for user in users:

                    if user != "":
                        self.online_list.insert(
                            tk.END,
                            user
                        )

            return

        if parts[0] == "MESSAGE":

            sender = parts[1]

            content = parts[2]

            self.show_chat(
                f"{sender}: {content}"
            )

            return

        self.show_chat(message)

    # ==================================
    # CHAT
    # ==================================

    def show_chat(self, text):

        self.chat_box.config(
            state="normal"
        )

        self.chat_box.insert(
            tk.END,
            text + "\n"
        )

        self.chat_box.see(
            tk.END
        )

        self.chat_box.config(
            state="disabled"
        )

    # ==================================
    # CLEAR
    # ==================================

    def clear_chat(self):

        self.chat_box.config(
            state="normal"
        )

        self.chat_box.delete(
            "1.0",
            tk.END
        )

        self.chat_box.config(
            state="disabled"
        )


if __name__ == "__main__":

    ChatWindow()