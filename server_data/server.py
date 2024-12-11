import socket
import threading
import os
import tkinter as tk
from tkinter import messagebox, ttk
from openpyxl import Workbook, load_workbook
import time
import logging

PORT = 12345
HEADER = 64
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
FILE_UPLOAD_FILE_MESSAGE = "!UPLOAD_FILE"
FILE_UPLOAD_FOLDER_MESSAGE="!UPLOAD_FOLDER"
FILE_LIST_REQUEST = "!LIST"
FILE_DOWNLOAD_REQUEST = "!DOWNLOAD"
SERVER = "0.0.0.0"
#SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)

all_connections = []

#Socket của server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(ADDR)

#File hoạt động của server
log_directory = "server_data/PRIVATE"
os.makedirs(log_directory, exist_ok=True)
log_file_path = os.path.join(log_directory, "server_log.txt")
logging.basicConfig(
    filename=log_file_path,  # Sử dụng đường dẫn đầy đủ
    level=logging.INFO,      # Mức độ log
    format="%(asctime)s - %(levelname)s - %(message)s",  # Định dạng log
    filemode="a"             # Append mode (ghi thêm vào file)
)

# Folder của server
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

##################################################################################################################################
# Đăng nhập 
def create_or_load_user_db():
    # Đường dẫn đến thư mục PRIVATE
    os.makedirs(private_folder, exist_ok=True)  # Tạo thư mục nếu chưa tồn tại

    # Đường dẫn đầy đủ đến file user_data.xlsx
    file_name = os.path.join(private_folder, "user_data.xlsx")

    try:
        if not os.path.exists(file_name):
            # Tạo file mới và thêm tiêu đề
            wb = Workbook()
            sheet = wb.active
            sheet.append(["Username", "Password"])  # Thêm tiêu đề
            wb.save(file_name)  # Lưu file
        else:
            # Mở file nếu đã tồn tại
            wb = load_workbook(file_name)
        return wb
    except Exception as e:
        print(f"Lỗi khi mở hoặc tạo file: {e}")
        return None

def register(username, password):
    """
    Đăng ký tài khoản, lưu vào file Excel trong thư mục PRIVATE.
    """
    # Đường dẫn tới file trong thư mục PRIVATE
    os.makedirs(private_folder, exist_ok=True)  # Đảm bảo thư mục tồn tại
    file_name = os.path.join(private_folder, "user_data.xlsx")

    # Tải hoặc tạo file Excel
    wb = create_or_load_user_db()
    sheet = wb.active

    # Kiểm tra nếu username đã tồn tại
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if row[0] == username:
            print("Tài khoản đã tồn tại.")
            return False

    # Nếu không tồn tại, thêm tài khoản mới vào file
    sheet.append([username, password])
    wb.save(file_name)  # Lưu vào file với đường dẫn đúng
    print("Đăng ký thành công!")
    return True


def login(username, password):
    """
    Đăng nhập, kiểm tra tài khoản trong file Excel tại thư mục PRIVATE.
    """
    # Đường dẫn tới file trong thư mục PRIVATE
    os.makedirs(private_folder, exist_ok=True)  # Đảm bảo thư mục tồn tại
    file_name = os.path.join(private_folder, "user_data.xlsx")

    # Tải file Excel
    wb = create_or_load_user_db()
    sheet = wb.active

    # Kiểm tra tài khoản và mật khẩu
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if row[0] == username and row[1] == password:
            print("Đăng nhập thành công!")
            return True
    print("Đăng nhập thất bại!")
##################################################################################################################################
# KẾT NỐI
def server_listen():
    while True:
        conn, addr = server.accept()
        all_connections.append(conn)
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.daemon =True
        thread.start()
##################################################################################################################################
# CLIENT DOWNLOAD
def build_folder_tree(folder_path):
    """
    Xây dựng cây thư mục với nhiều nhánh từ thư mục gốc, bao gồm cả các tệp và thư mục con.
    Chỉ lấy phần cuối của folder_path (tên thư mục cuối cùng).
    """
    # Lấy phần cuối của folder_path
    base_folder = os.path.basename(folder_path)

    # Khởi tạo cây thư mục chỉ với phần cuối của folder_path
    folder_tree = {base_folder: {}}

    # Duyệt qua thư mục gốc và các thư mục con
    for root, dirs, files in os.walk(folder_path):
        # Tính toán đường dẫn tương đối từ thư mục gốc
        relative_path = os.path.relpath(root, folder_path)
        
        # Nếu đường dẫn là thư mục gốc thì tạo node cho thư mục gốc
        parts = relative_path.split(os.sep) if relative_path != '.' else []

        # Duyệt qua các phần tử của đường dẫn tương đối và xây dựng cây
        node = folder_tree[base_folder]  # Bắt đầu từ thư mục cuối cùng
        for part in parts:
            node = node.setdefault(part, {})

        # Thêm các tệp vào thư mục tương ứng
        for file in files:
            node[file] = None  # Các tệp sẽ không có giá trị con, nên ta gán giá trị None

        # Thêm thư mục con vào nếu có
        for dir in dirs:
            if dir not in node:
                node[dir] = {}

    return folder_tree 

def handle_download_file(conn,addr,msg):
    filename = msg.split(" ", 1)[1]
    # Xác định đường dẫn tuyệt đối của file trong thư mục PUBLIC
    file_path = os.path.abspath(os.path.join(folder_path, filename))
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
                    conn.sendall(file_data)
            logging.info(f"Download Successful: \"{filename}\" from client {addr}")
        else:
            conn.send("File not found.".encode(FORMAT))
            logging.error(f"Download Unsuccessful: \"{filename}\" from client {addr}")
    else:
    # Nếu file yêu cầu nằm ngoài thư mục PUBLIC (tức là trong PRIVATE hoặc thư mục khác)
        if os.path.commonpath([file_path, private_folder_path]) == private_folder_path:
            conn.send("File not found.".encode(FORMAT))
            logging.warning(f"Download Unsuccessful: \"{filename}\" from client {addr}")
##################################################################################################################################
# CLIENT UPLOAD FILE
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

def get_unique_filename(file_path):
    if not os.path.exists(file_path):
        return file_path

    base, ext = os.path.splitext(file_path)
    counter = 1
    while True:
        new_file_path = f"{base}({counter}){ext}"
        if not os.path.exists(new_file_path):
            return new_file_path
        counter += 1
          
def handle_file_upload(conn, addr, msg):
    file_name = msg.split(" ", 1)[1]
    file_length = int(conn.recv(HEADER).decode(FORMAT)) 

    # Xác định đường dẫn file ban đầu
    file_path = os.path.join(public_folder, file_name)
    # Đổi tên file nếu trùng
    unique_file_path = get_unique_filename(file_path)

    # Đảm bảo tất cả thư mục trong đường dẫn tồn tại
    directory = os.path.dirname(unique_file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)  # Tạo tất cả thư mục cha

    # Nhận dữ liệu từ client và lưu vào file
    total_received = 0
    with open(unique_file_path, "wb") as file:
        while total_received < file_length:
            file_data = conn.recv(1024)
            if not file_data:
                break
            total_received += len(file_data)
            file.write(file_data)

    # Ghi log khi upload thành công
    logging.info(f"Upload Successful: \"{unique_file_path}\" from client {addr}")


##################################################################################################################################
# CLIENT UPLOAD FOLDER
def handle_folder_upload(conn, addr):
    try:
        # Nhận độ dài tên thư mục
        folder_name_length = int(conn.recv(HEADER).decode(FORMAT))
        folder_name = conn.recv(folder_name_length).decode(FORMAT)  # Nhận tên thư mục

        # Tạo thư mục trong PUBLIC
        folder_path2 = os.path.join(public_folder, folder_name)
        if not os.path.exists(folder_path2):
            os.makedirs(folder_path2)

        logging.info(f"Starting to receive folder: {folder_name} from client {addr}")

        # Nhận số lượng file trong thư mục
        #num_files_msg = int(conn.recv(HEADER).decode(FORMAT))
        #num_files = conn.recv(num_files_msg).decode(FORMAT)
        num_files = int(conn.recv(HEADER).decode(FORMAT))
        
        print(num_files)
        
        for _ in range(num_files):
            # Nhận thông tin file
            file_name_length = int(conn.recv(HEADER).decode(FORMAT))
            file_name = conn.recv(file_name_length).decode(FORMAT)

            # Nhận và lưu file
            file_path = os.path.join(folder_path2, file_name)
            file_length = int(conn.recv(HEADER).decode(FORMAT))
            total_received = 0

            file_directory = os.path.dirname(file_path)
            if not os.path.exists(file_directory):
                os.makedirs(file_directory)

            with open(file_path, "wb") as file:
                while total_received < file_length:
                    file_data = conn.recv(1024)
                    if not file_data:
                        logging.error(f"Error receiving data for file {file_name}")
                        break
                    total_received += len(file_data)
                    file.write(file_data)

            logging.info(f"File \"{file_name}\" uploaded successfully.")

        logging.info(f"Folder \"{folder_name}\" uploaded successfully from client {addr}")

    except Exception as e:
        logging.error(f"Error during folder upload from {addr}: {e}")
        conn.send("Error during upload.".encode(FORMAT))

def handle_data(conn):
    try:
        data = conn.recv(1024)
        if data:
            try:
                text_data = data.decode(FORMAT)
                print(f"Received text data: {text_data}")
            except UnicodeDecodeError:
                print("Received non-text data, saving as binary.")
                with open('received_file', 'wb') as file:
                    file.write(data)
        else:
            print("No data received.")
    except Exception as e:
        print(f"Error receiving data: {e}") 

##################################################################################################################################
# XỬ LÍ CLIENT
def handle_client(conn, addr):
    global connected_clients
    print(f"[NEW CONNECTION] {addr} connected.")
    
    connected_clients += 1
    print(f"[ACTIVE CONNECTIONS] {connected_clients} active connections.")
    logging.info(f"Connect from client {addr}")

    logged_in = False  # Trạng thái chưa đăng nhập

    try:
        while True:
            # Nhận chiều dài thông điệp
                msg_length = conn.recv(HEADER)
                if not msg_length:
                    break
                
                # Nếu msg_length là byte, chúng ta chỉ decode khi chắc chắn đó là chuỗi văn bản
                try:
                    msg_length = msg_length.decode(FORMAT)
                except UnicodeDecodeError:
                    # Nếu có lỗi giải mã, có thể đó là dữ liệu nhị phân, chúng ta sẽ bỏ qua
                    logging.error(f"Received non-text data, skipping decoding.")
                    break
                
                msg_length = int(msg_length)  # Chuyển đổi chiều dài thông điệp thành số
                msg = conn.recv(msg_length)

                # Nếu thông điệp không thể giải mã được
                try:
                    msg = msg.decode(FORMAT)
                except UnicodeDecodeError:
                    logging.error(f"Received corrupted data: {msg[:50]}...")
                    break
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
                    
                    #List file
                    if msg.startswith(FILE_LIST_REQUEST):
                        folder_tree = build_folder_tree(public_folder)
                        folder_data = str(folder_tree)
                        conn.sendall(folder_data.encode(FORMAT))
                        conn.send(b"EOF")
                        logging.info(FILE_LIST_REQUEST + f" from client {addr}")
                        
                    # Upload file
                    elif msg.startswith(FILE_UPLOAD_FILE_MESSAGE):
                        handle_file_upload(conn,addr,msg)
                        
                    # Upload folder
                    elif msg.startswith(FILE_UPLOAD_FOLDER_MESSAGE):
                        handle_folder_upload(conn, addr)
                        
                    # Download file
                    elif msg.startswith(FILE_DOWNLOAD_REQUEST):
                        handle_download_file(conn,addr,msg)
                    else:
                        conn.send("Invalid command.".encode(FORMAT))
    except Exception as e:
        print(f"Lỗi: {e}")
        pass
    finally:
        all_connections.remove(conn)
        conn.close()
        connected_clients -= 1
        logging.info(f"!!Disconnect from client {addr}")
        print(f"[ACTIVE CONNECTIONS] {connected_clients} active connections.")

##################################################################################################################################
# GIAO DIỆN
def clear_text_box(chat_box):
    chat_box.config(state="normal")
    chat_box.delete(1.0, tk.END)
    chat_box.config(state="disabled")
    
def history_log():
    pass

def current_time():
    cur_time = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
    return str(cur_time) + ": "

def list_all_connecting():
    chat_box.config(state="normal")
    if not all_connections:
        chat_box.insert(tk.END,current_time()+"Không có kết nối\n")
    else: 
        chat_box.insert(tk.END,current_time()+"Tất cả các kết nối là:\n")
        for conn in all_connections:
            try:
                addr=conn.getpeername()
                chat_box.insert(tk.END,f"  Client {addr} đang kết nối\n")
            except Exception as e:
                chat_box.insert(tk.END,f"  Lỗi khi lấy thông tin kết nối: {e}\n")
    chat_box.config(state="disabled")
  
def closing_window():
    if messagebox.askokcancel("Thoát", "Bạn có muốn ngắt kết nối ??"):
        try: 
            if server.fileno() != -1: 
                server.close()
        finally:
            root.destroy()
    os._exit(0)

    
print("[STARTING] Server is starting...")
server.listen()
print(f"[LISTENING] Server is listening on {SERVER}")
logging.info("Server Start!!") #Ghi vào file log
# Khởi tạo cửa sổ Tkinter
global root
root = tk.Tk()
root.title("Server Interface")
root.geometry("700x500")

root.protocol("WM_DELETE_WINDOW", closing_window)
# Xử lý dữ liệu  
handle_server = threading.Thread(target=server_listen)
handle_server.daemon = True # Dừng Thread khi đóng giao diện
handle_server.start()

# Xử lí giao diện

chat_box = tk.Text(root, bg="light yellow",height = 15,width=75,state="disabled", wrap=tk.WORD)
chat_box.grid(row=0, column=0, columnspan=10, padx=10, pady=10)

scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=chat_box.yview)
scrollbar.grid(row=0, column=10,sticky="ns")
chat_box.config(yscrollcommand=scrollbar.set)

button_clear_text_box = tk.Button(root, text="Clear all text", command=lambda: clear_text_box(chat_box))
button_clear_text_box.grid(row=2, column=0, padx=10, pady=10)

button_all_connected = tk.Button(root, text="ALL connected", command=list_all_connecting)
button_all_connected.grid(row=3, column=0, padx=10, pady=10)

button_history_log = tk.Button(root, text="History log", command=history_log)
button_history_log.grid(row=4, column=0, padx=10, pady=10)

root.mainloop() 
