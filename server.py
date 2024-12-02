import socket
import threading
import os

PORT = 8080
HEADER = 64
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
FILE_TRANSFER_MESSAGE = "!FILE"
FILE_LIST_REQUEST = "!LIST"
FILE_DOWNLOAD_REQUEST = "!DOWNLOAD"
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(ADDR)

folder_path = "server_data"
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    try:
        while True:
            msg_length = conn.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                msg = conn.recv(msg_length).decode(FORMAT)

                if msg == DISCONNECT_MESSAGE:
                    break
                elif msg.startswith(FILE_LIST_REQUEST):
                    # Gửi danh sách file từ thư mục server_data
                    files = os.listdir(folder_path)
                    files_list = "\n".join(files) if files else "No files available."
                    conn.send(files_list.encode(FORMAT))
                elif msg.startswith(FILE_DOWNLOAD_REQUEST):
                    # Xử lý tải file
                    filename = msg.split()[1]
                    file_path = os.path.join(folder_path, filename)

                    if os.path.exists(file_path):
                        conn.send(filename.encode(FORMAT))
                        file_size = os.path.getsize(file_path)
                        conn.send(str(file_size).encode(FORMAT))

                        with open(file_path, "rb") as f:
                            file_data = f.read()
                            conn.send(file_data)
                    else:
                        conn.send("File not found.".encode(FORMAT))
                elif msg.startswith(FILE_TRANSFER_MESSAGE):
                    # Xử lý nhận file từ client
                    filename = msg.split()[1]
                    file_length = int(conn.recv(HEADER).decode(FORMAT))
                    file_data = conn.recv(file_length)

                    file_path = os.path.join(folder_path, filename)
                    with open(file_path, "wb") as f:
                        f.write(file_data)

                    conn.send(f"File {filename} đã được nhận và lưu thành công.".encode(FORMAT))
                else:
                    print(f"[{addr}] Received invalid message: {msg}")
    finally:
        conn.close()

def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

print("[STARTING] Server is starting...")
start()
