import socket
import os
from tkinter import Tk
from tkinter.filedialog import askopenfilename

PORT = 8080
HEADER = 64
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
FILE_TRANSFER_MESSAGE = "!FILE"  # Thông báo gửi file
FILE_LIST_REQUEST = "!LIST"  # Yêu cầu danh sách file từ server
FILE_DOWNLOAD_REQUEST = "!DOWNLOAD"  # Yêu cầu tải file từ server

SERVER = "192.168.137.227"  # Địa chỉ IP của server
ADDR = (SERVER, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)  # Kết nối đến server

def send_message(msg):
    """
    Gửi một tin nhắn dạng text đến server
    """
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)  # Gửi độ dài tin nhắn
    client.send(message)  # Gửi tin nhắn

def send_file(file_path):
    """
    Gửi một file đến server
    """
    # Gửi thông báo FILE_TRANSFER_MESSAGE để báo hiệu gửi file
    send_message(f"{FILE_TRANSFER_MESSAGE} {file_path.split('/')[-1]}")

    # Đọc dữ liệu file và gửi đến server
    with open(file_path, "rb") as file:
        file_data = file.read()
        file_length = len(file_data)

        # Gửi độ dài dữ liệu file
        send_length = str(file_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        client.send(send_length)

        # Gửi nội dung file
        client.send(file_data)

    print(f"File {file_path.split('/')[-1]} đã được gửi.")
    # Nhận phản hồi từ server
    print(f"From server: {client.recv(2048).decode(FORMAT)}")

def download_file(filename):
    """
    Yêu cầu server gửi file về client
    """
    # Gửi yêu cầu tải file
    send_message(f"{FILE_DOWNLOAD_REQUEST} {filename}")

    # Nhận thông báo và kích thước file
    file_name = client.recv(HEADER).decode(FORMAT)
    file_size = int(client.recv(HEADER).decode(FORMAT))

    if file_name == "File not found.":
        print("File không tồn tại trên server.")
    else:
        print(f"Đang tải xuống file: {file_name}, kích thước: {file_size} bytes")
        with open(f"client_data/{file_name}", "wb") as file:
            total_received = 0
            while total_received < file_size:
                file_data = client.recv(1024)
                total_received += len(file_data)
                file.write(file_data)
            print(f"File {file_name} đã được tải xuống.")

def list_files():
    """
    Yêu cầu server gửi danh sách các file có sẵn để tải xuống hoặc upload
    """
    send_message(FILE_LIST_REQUEST)  # Yêu cầu server gửi danh sách file

    # Nhận danh sách các file từ server
    files = client.recv(1024).decode(FORMAT)
    if files:
        return files.split("\n")
    else:
        print("Không có file nào trên server.")
        return []

# Mở hộp thoại để chọn file và gửi hoặc tải
Tk().withdraw()  # Ẩn cửa sổ chính của Tkinter
while True:
    choice = input("Bạn muốn gửi (upload) hay tải (download) file: ").lower()
    if choice == "upload":
        # Chọn file upload từ máy tính client
        file_path = askopenfilename(title="Chọn file để gửi")  # Chọn file bằng hộp thoại
        if file_path:
            send_file(file_path)  # Gửi file đã chọn lên server
        else:
            print("Không có file nào được chọn.")
    elif choice == "download":
        # Lấy danh sách các file có sẵn từ server
        files = list_files()

        if files:
            # Cho phép người dùng chọn file bằng giao diện đồ họa
            file_to_download = askopenfilename(title="Chọn file để tải xuống", initialdir="server_data", filetypes=[("All files", "*.*")])

            if file_to_download:
                # Chỉ lấy tên file, không cần đường dẫn đầy đủ
                file_to_download = file_to_download.split("/")[-1]
                download_file(file_to_download)  # Tải file đã chọn từ server
            else:
                print("Không có file nào được chọn.")
    else:
        print("Lựa chọn không hợp lệ.")
        break

# Đóng kết nối
client.close()
