import socket
import os
from tkinter import Tk, Button, filedialog, Label, Entry, StringVar, messagebox
import tkinter.simpledialog as simpledialog
PORT = 8080
HEADER = 64
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
FILE_TRANSFER_MESSAGE = "!FILE"
FILE_LIST_REQUEST = "!LIST"
FILE_DOWNLOAD_REQUEST = "!DOWNLOAD"
REGISTER_REQUEST = "!REGISTER"
LOGIN_REQUEST = "!LOGIN"
FOLDER_DOWNLOAD_REQUEST = "!FOLDER_DOWNLOAD"
FOLDER_TRANSFER_MESSAGE = "!FOLDER" # Yêu cầu tải folder

SERVER = "192.168.222.234"  # Địa chỉ IP của server
ADDR = (SERVER, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def connect_to_server():
    try:
        client.connect(ADDR)
        print("Kết nối đến server thành công.")
    except Exception as e:
        print(f"Không thể kết nối đến server: {e}")
        return False
    return True


def send_message(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)


def receive_message():
    return client.recv(2048).decode(FORMAT)


def register(username, password):
    send_message(f"{REGISTER_REQUEST} {username} {password}")
    response = receive_message()
    messagebox.showinfo("Register", response)


def login(username, password):
    send_message(f"{LOGIN_REQUEST} {username} {password}")
    response = receive_message()
    if "success" in response.lower():
        messagebox.showinfo("Login", "Đăng nhập thành công!")
        return True
    else:
        messagebox.showerror("Login", "Đăng nhập thất bại!")
        return False


def send_file(file_path):
    send_message(f"{FILE_TRANSFER_MESSAGE} {os.path.basename(file_path)}")

    with open(file_path, "rb") as file:
        file_data = file.read()
        file_length = len(file_data)

        send_length = str(file_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        client.send(send_length)

        client.send(file_data)

    print(f"File {os.path.basename(file_path)} đã được gửi.")
    messagebox.showinfo("Upload", f"File {os.path.basename(file_path)} đã được gửi.")


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

# Upload folder
def send_folder(folder_path):
    zip_name = os.path.basename(folder_path) + ".zip"
    with zipfile.ZipFile(zip_name, 'w') as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), folder_path))
    send_message(f"{FOLDER_TRANSFER_MESSAGE} {zip_name}")
    with open(zip_name, "rb") as f:
        zip_data = f.read()
        send_length = str(len(zip_data)).encode(FORMAT) + b' ' * (HEADER - len(str(len(zip_data)).encode(FORMAT)))
        client.send(send_length)
        client.sendall(zip_data)
    os.remove(zip_name)

# Download folder
def download_folder(folder_name):
    send_message(f"{FOLDER_DOWNLOAD_REQUEST} {folder_name}")
    folder_name = client.recv(HEADER).decode(FORMAT).strip()
    folder_size = int(client.recv(HEADER).decode(FORMAT).strip())

    if not os.path.exists("client_data"):
        os.makedirs("client_data") # Tạo thư mục client_data nếu chưa tồn tại
    
    folder_path = os.path.join("client_data", folder_name)
    with open(folder_path + ".zip", "wb") as f:
        while folder_size > 0:
            data = client.recv(min(1024, folder_size))
            f.write(data)
            folder_size -= len(data)
    print(f"Folder {folder_name} đã được tải xuống.")

###
def upload_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        send_folder(folder_path)
        
def download_folder_gui():
    folder_name = filedialog.askdirectory()
    if folder_name:
        download_folder(folder_name)
###

# Giao diện Tkinter
root = Tk()
root.title("File Upload/Download")
username_var = StringVar()
password_var = StringVar()


def on_register_button_click():
    username = username_var.get()
    password = password_var.get()
    if username and password:
        register(username, password)
    else:
        messagebox.showerror("Error", "Vui lòng nhập đầy đủ thông tin.")


def on_login_button_click():
    username = username_var.get()
    password = password_var.get()
    if username and password:
        if login(username, password):
            show_file_buttons()
    else:
        messagebox.showerror("Error", "Vui lòng nhập đầy đủ thông tin.")


def show_file_buttons():
    upload_button.pack(pady=10)
    download_button.pack(pady=10)
    close_button.pack(pady=10)
    login_button.pack_forget()
    register_button.pack_forget()
    username_label.pack_forget()
    password_label.pack_forget()
    username_entry.pack_forget()
    password_entry.pack_forget()



# Nút Upload
def on_upload_button_click():
    file_path = filedialog.askopenfilename(title="Chọn file để gửi")  # Chọn file từ máy tính
    if file_path:
        send_file(file_path)  # Gửi file đã chọn lên server
    else:
        print("Không có file nào được chọn.")

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

def close_connection():
    if client.fileno() != -1:  # Kiểm tra nếu socket vẫn còn hoạt động
        send_message(DISCONNECT_MESSAGE)  # Gửi tin nhắn ngắt kết nối đến server
        client.close()  # Đóng kết nối
        print("Kết nối đã được đóng.")
    else:
        print("Kết nối đã bị đóng trước đó.")
    root.quit()  # Đóng cửa sổ Tkinter sau khi ngắt kết nối


# Giao diện Đăng nhập / Đăng ký
username_label = Label(root, text="Username")
username_label.pack()
username_entry = Entry(root, textvariable=username_var)
username_entry.pack()

password_label = Label(root, text="Password")
password_label.pack()
password_entry = Entry(root, textvariable=password_var, show="*")
password_entry.pack()

login_button = Button(root, text="Login", command=on_login_button_click, bg="blue", fg="white", font=("Arial", 12))
login_button.pack(pady=10)

register_button = Button(root, text="Register", command=on_register_button_click, bg="green", fg="white", font=("Arial", 12))
register_button.pack(pady=10)

# Nút Upload và Download chỉ hiển thị khi đăng nhập thành công
upload_button = Button(root, text="Upload File", command=on_upload_button_click, bg="green", fg="white", font=("Arial", 12))
download_button = Button(root, text="Download File", command=on_download_button_click, bg="blue", fg="white", font=("Arial", 12))

close_button = Button(root, text="Close Connection", command=close_connection, bg="red", fg="white", font=("Arial", 12))

# Kết nối đến server
if not connect_to_server():
    root.quit()

root.mainloop()
