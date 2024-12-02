import socket
import os
from tkinter import Tk, Button, filedialog, Label

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

def connect_to_server():
    try:
        client.connect(ADDR)  # Kết nối đến server
        print("Kết nối đến server thành công.")
    except Exception as e:
        print(f"Không thể kết nối đến server: {e}")
        return False
    return True

def send_message(msg):
    """
    Gửi một tin nhắn dạng text đến server
    """
    if client.fileno() == -1:  # Kiểm tra nếu socket đã bị đóng
        print("Socket đã bị đóng, không thể gửi tin nhắn.")
        return

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
    send_message(f"{FILE_TRANSFER_MESSAGE} {file_path.split('/')[-1]}")

    with open(file_path, "rb") as file:
        file_data = file.read()
        file_length = len(file_data)

        send_length = str(file_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        client.send(send_length)

        client.send(file_data)

    print(f"File {file_path.split('/')[-1]} đã được gửi.")
    print(f"From server: {client.recv(2048).decode(FORMAT)}")

def download_file(filename):
    """
    Yêu cầu server gửi file về client
    """
    send_message(f"{FILE_DOWNLOAD_REQUEST} {filename}")

    # Nhận tên file và kích thước file từ server
    file_name = client.recv(HEADER).decode(FORMAT)
    file_size = int(client.recv(HEADER).decode(FORMAT))

    if file_name == "File not found.":
        print("File không tồn tại trên server.")
    else:
        print(f"Đang tải xuống file: {file_name}, kích thước: {file_size} bytes")

        # Tạo thư mục client_data nếu chưa có
        if not os.path.exists('client_data'):
            os.makedirs('client_data')

        # Mở file và bắt đầu tải xuống
        with open(f"client_data/{file_name}", "wb") as file:
            total_received = 0
            while total_received < file_size:
                file_data = client.recv(1024)
                total_received += len(file_data)
                file.write(file_data)
                # Hiển thị tiến trình tải xuống (tuỳ chọn)
                print(f"Đã nhận {total_received} / {file_size} bytes")

            print(f"File {file_name} đã được tải xuống thành công.")

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


# Tạo giao diện Tkinter
root = Tk()
root.title("File Upload/Download")

# Nút Upload
def on_upload_button_click():
    file_path = filedialog.askopenfilename(title="Chọn file để gửi")  # Chọn file từ máy tính
    if file_path:
        send_file(file_path)  # Gửi file đã chọn lên server
    else:
        print("Không có file nào được chọn.")

upload_button = Button(root, text="Upload File", command=on_upload_button_click, bg="green", fg="white", font=("Arial", 12))
upload_button.pack(pady=20)

# Nút Download
def on_download_button_click():
    files = list_files()  # Lấy danh sách các file có sẵn từ server
    if files:
        # Cho phép người dùng chọn file bằng giao diện đồ họa
        file_to_download = filedialog.askopenfilename(title="Chọn file để tải xuống", initialdir="server_data", filetypes=[("All files", "*.*")])

        if file_to_download:
            # Chỉ lấy tên file, không cần đường dẫn đầy đủ
            file_to_download = file_to_download.split("/")[-1]
            download_file(file_to_download)  # Tải file đã chọn từ server
        else:
            print("Không có file nào được chọn.")

download_button = Button(root, text="Download File", command=on_download_button_click, bg="blue", fg="white", font=("Arial", 12))
download_button.pack(pady=20)

# Nút Đóng kết nối
def close_connection():
    if client.fileno() != -1:  # Kiểm tra nếu socket vẫn còn hoạt động
        send_message(DISCONNECT_MESSAGE)  # Gửi tin nhắn ngắt kết nối đến server
        client.close()  # Đóng kết nối
        print("Kết nối đã được đóng.")
    else:
        print("Kết nối đã bị đóng trước đó.")
    root.quit()  # Đóng cửa sổ Tkinter sau khi ngắt kết nối

close_button = Button(root, text="Close Connection", command=close_connection, bg="red", fg="white", font=("Arial", 12))
close_button.pack(pady=20)

# Kết nối tới server
if not connect_to_server():
    root.quit()  # Nếu không kết nối được server thì đóng cửa sổ

root.mainloop()
