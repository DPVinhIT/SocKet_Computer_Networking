import logging.config
import socket
import threading
import os
from tkinter import Tk
from tkinter import messagebox
from openpyxl import Workbook, load_workbook
import zipfile
import time
import logging

PORT = 8080
HEADER = 64
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
FILE_TRANSFER_MESSAGE = "!FILE"
FILE_LIST_REQUEST = "!LIST"
FILE_DOWNLOAD_REQUEST = "!DOWNLOAD"
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)

#Socket của server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(ADDR)

#File hoạt động của server
logging.basicConfig(
    filename="server_log.txt",  # Đường dẫn đến file lưu log
    level=logging.INFO,         # Mức độ log: INFO, WARNING, ERROR
    format="%(asctime)s - %(levelname)s - %(message)s",  # Định dạng log, bao gồm thời gian
    filemode="a"
)

#Folder của server
folder_path = "server_data"
if not os.path.exists(folder_path):
    os.makedirs(folder_path)
public_folder = os.path.join(folder_path, "PUBLIC")
private_folder = os.path.join(folder_path, "PRIVATE")
if not os.path.exists(public_folder):
    os.makedirs(public_folder)
if not os.path.exists(private_folder):
    os.makedirs(private_folder)

connected_clients = 0  # Biến đếm số lượng kết nối
def send_file_to_client(client_socket, filename):
    try:
        # Kiểm tra nếu file tồn tại
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            
            # Gửi tên file và kích thước file
            client_socket.send(filename.encode(FORMAT))
            client_socket.send(str(file_size).encode(FORMAT))  # Gửi kích thước file như một số nguyên

            # Đọc file và gửi dữ liệu
            with open(filename, 'rb') as file:
                file_data = file.read(1024)  # Đọc file từng phần (1024 bytes)
                while file_data:
                    client_socket.send(file_data)
                    file_data = file.read(1024)  # Tiếp tục đọc file từng phần

            print(f"File {filename} đã được gửi thành công.")
        else:
            # Gửi thông báo file không tồn tại
            client_socket.send("File not found.".encode(FORMAT))
    except Exception as e:
        print(f"Error sending file: {e}")
        client_socket.send("Error while sending file.".encode(FORMAT))


def create_or_load_user_db():
    file_name = "user_data.xlsx"
    try:
        if not os.path.exists(file_name):
            # Tạo file mới và thêm tiêu đề
            wb = Workbook()
            sheet = wb.active
            sheet.append(["Username", "Password"])
            wb.save(file_name)
        else:
            wb = load_workbook(file_name)
        return wb
    except Exception as e:
        print(f"Lỗi khi mở hoặc tạo file: {e}")
        return None

def register(username, password):
    """
    Đăng ký tài khoản, lưu vào file Excel
    """
    wb = create_or_load_user_db()
    sheet = wb.active

    # Kiểm tra nếu username đã tồn tại
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if row[0] == username:
            print("Tài khoản đã tồn tại.")
            return False
    # Nếu không tồn tại, thêm tài khoản mới vào file
    sheet.append([username, password])
    wb.save("user_data.xlsx")
    print("Đăng ký thành công!")
    return True

def login(username, password):
    """
    Đăng nhập, kiểm tra tài khoản trong file Excel
    """
    wb = create_or_load_user_db()
    sheet = wb.active

    # Kiểm tra tài khoản và mật khẩu
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if row[0] == username and row[1] == password:
            print("Đăng nhập thành công!")
            return True
    print("Đăng nhập thất bại!")

import os

def handle_client(conn, addr, root):
    global connected_clients
    print(f"[NEW CONNECTION] {addr} connected.")
    
    connected_clients += 1
    print(f"[ACTIVE CONNECTIONS] {connected_clients} active connections.")
    logging.info(f"Connect from client {addr}")

    logged_in = False  # Trạng thái chưa đăng nhập

    try:
        while True:
            msg_length = conn.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                msg = conn.recv(msg_length).decode(FORMAT)

                if msg == DISCONNECT_MESSAGE:
                    break

                # Nếu chưa đăng nhập
                if not logged_in:
                    if msg.startswith("!REGISTER"):
                        try:
                            _, username, password = msg.split(" ", 2)
                            if register(username, password):
                                conn.send("Registration successful.".encode(FORMAT))
                            else:
                                conn.send("Registration failed. Username already exists.".encode(FORMAT))
                        except ValueError:
                            conn.send("Invalid format. Use: !REGISTER <username> <password>".encode(FORMAT))

                    elif msg.startswith("!LOGIN"):
                        try:
                            _, username, password = msg.split(" ", 2)
                            if login(username, password):
                                conn.send("Login successful.".encode(FORMAT))
                                logged_in = True
                            else:
                                conn.send("Login failed.".encode(FORMAT))
                        except ValueError:
                            conn.send("Invalid format. Use: !LOGIN <username> <password>".encode(FORMAT))
                    else:
                        conn.send("Please login or register first.".encode(FORMAT))

                else:
                    # Xử lý các yêu cầu sau khi đã đăng nhập
                    if msg.startswith(FILE_LIST_REQUEST):
                         # Chỉ truy cập thư mục PUBLIC
                        files = os.listdir(public_folder)
                        files_list = "\n".join(files) if files else "No files available."
                        conn.send(files_list.encode(FORMAT))
                        logging.info(FILE_LIST_REQUEST + f" from client {addr}")
                    # Upload file
                    elif msg.startswith(FILE_TRANSFER_MESSAGE):
                        filename=msg.split(" ",1)[1]
                        file_length = int(conn.recv(HEADER).decode(FORMAT)) 
                        file_data = conn.recv(file_length)
                        file_path = os.path.join(public_folder,filename)
                        with open(file_path, "wb") as f:
                            f.write(file_data)
                        logging.info(f"Upload Successful: \"{filename}\" from client {addr}")
                    # Download file
                    elif msg.startswith(FILE_DOWNLOAD_REQUEST):
                        filename = msg.split(" ", 1)[1]
                        # Xác định đường dẫn tuyệt đối của file trong thư mục PUBLIC
                        file_path = os.path.abspath(os.path.join(folder_path, "PUBLIC", filename))
                        # Đường dẫn tuyệt đối của thư mục PUBLIC
                        public_folder_path = os.path.abspath(os.path.join(folder_path, "PUBLIC"))
                        # Đường dẫn tuyệt đối của thư mục PRIVATE
                        private_folder_path = os.path.abspath(os.path.join(folder_path, "PRIVATE"))
                        # So sánh các đường dẫn của file với thư mục PUBLIC
                        if not os.path.relpath(file_path, public_folder_path).startswith(os.pardir):
                        # Nếu không nằm ngoài thư mục PUBLIC
                            if os.path.exists(file_path):
                                conn.send(filename.encode(FORMAT))
                                file_size = os.path.getsize(file_path)
                                conn.send(str(file_size).encode(FORMAT))

                                with open(file_path, "rb") as f:
                                    while True:
                                        file_data = f.read(1024)
                                        if not file_data:
                                            break
                                        conn.send(file_data)
                                logging.info(f"Download Successful: \"{filename}\" from client {addr}")
                            else:
                                conn.send("File not found.".encode(FORMAT))
                                logging.error(f"Download Unsuccessful: \"{filename}\" from client {addr}")
                        else:
                        # Nếu file yêu cầu nằm ngoài thư mục PUBLIC (tức là trong PRIVATE hoặc thư mục khác)
                            if os.path.commonpath([file_path, private_folder_path]) == private_folder_path:
                                conn.send("File not found.".encode(FORMAT))
                                logging.warning(f"Download Unsuccessful: \"{filename}\" from client {addr}")

                    else:
                        conn.send("Invalid command.".encode(FORMAT))

    finally:
        conn.close()
        connected_clients -= 1
        logging.info(f"!!Disconnect from client {addr}")
        print(f"[ACTIVE CONNECTIONS] {connected_clients} active connections.")






# def handle_client(conn, addr):
#     print(f"[NEW CONNECTION] {addr} connected.")
#     clients.append(addr)  # Add client to the list
    
#     try:
#         while True:
#             msg_length = conn.recv(HEADER).decode(FORMAT)
#             if msg_length:
#                 msg_length = int(msg_length)
#                 msg = conn.recv(msg_length).decode(FORMAT)

#                 if msg == DISCONNECT_MESSAGE:
#                     break
#                 elif msg.startswith(FILE_LIST_REQUEST):
#                     files = os.listdir(folder_path)
#                     files_list = "\n".join(files) if files else "No files available."
#                     conn.send(files_list.encode(FORMAT))
#                 elif msg.startswith(FILE_DOWNLOAD_REQUEST):
#                     filename = msg.split()[1]
#                     file_path = os.path.join(folder_path, filename)

#                     if os.path.exists(file_path):
#                         conn.send(filename.encode(FORMAT))
#                         file_size = os.path.getsize(file_path)
#                         conn.send(str(file_size).encode(FORMAT))

#                         with open(file_path, "rb") as f:
#                             file_data = f.read()
#                             conn.send(file_data)
#                     else:
#                         conn.send("File not found.".encode(FORMAT))
#                 elif msg.startswith(FOLDER_DOWNLOAD_REQUEST):
#                     folder_name = msg.split()[1]
#                     folder_dir = os.path.join(folder_path, folder_name)

#                     if os.path.exists(folder_dir) and os.path.isdir(folder_dir):
#                         zip_name = folder_name + ".zip"
#                         with zipfile.ZipFile(zip_name, 'w') as zipf:
#                             for root, dirs, files in os.walk(folder_dir):
#                                 for file in files:
#                                     zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), folder_dir))

#                         conn.send(folder_name.encode(FORMAT))
#                         folder_size = os.path.getsize(zip_name)
#                         conn.send(str(folder_size).encode(FORMAT))

#                         with open(zip_name, "rb") as zip_file:
#                             zip_data = zip_file.read()
#                             conn.send(zip_data)

#                         os.remove(zip_name)
#                     else:
#                         conn.send("Folder not found.".encode(FORMAT))
#                 elif msg.startswith(FILE_TRANSFER_MESSAGE):
#                     filename = msg.split()[1]
#                     file_length = int(conn.recv(HEADER).decode(FORMAT))
#                     file_data = conn.recv(file_length)

#                     file_path = os.path.join(folder_path, filename)
#                     with open(file_path, "wb") as f:
#                         f.write(file_data)

#                     conn.send(f"File {filename} đã được nhận và lưu thành công.".encode(FORMAT))
#                 else:
#                     print(f"[{addr}] Received invalid message: {msg}")
#     finally:
#         conn.close()
#         clients.remove(addr)  # Remove client from the list
#         update_clients_list()
        
#         # if connected_clients == 0:
#         #     print("[INFO] No active connections. Closing the window.")
#         #     root.quit()


def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    logging.info("Server Start!!") #Ghi vào file log
    # Khởi tạo cửa sổ Tkinter
    root = Tk()
    root.title("Server Interface")
    
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr, root))
        thread.start()

    root.mainloop()  # Bắt đầu vòng lặp giao diện

print("[STARTING] Server is starting...")
start()
