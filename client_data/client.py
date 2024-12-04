import socket
import threading
import os
import zipfile
import time
from tkinter import Tk, Button, filedialog, Label, Entry, StringVar, messagebox, ttk, Toplevel
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

#SERVER = "192.168.222.234"  # Địa chỉ IP của server
SERVER = socket.gethostbyname(socket.gethostname()) #Lấy ip của máy vì chạy cùng 1 máy
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
    send_message(f"{FILE_TRANSFER_MESSAGE} {file_path.split('/')[-1]}")

    with open(file_path, "rb") as file:
        file_data = file.read()
        file_length = len(file_data)

        send_length = str(file_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        client.send(send_length)

        client.send(file_data)

    print(f"File {os.path.basename(file_path)} đã được gửi.")
    messagebox.showinfo(
        "Upload", f"File {os.path.basename(file_path)} đã được gửi.")


def download_file(filename):
    """
    Yêu cầu server gửi file về client, chỉ cho phép tải file từ thư mục PUBLIC
    """
    send_message(f"{FILE_DOWNLOAD_REQUEST} {filename}")

    # Nhận phản hồi đầu tiên từ server (tên file hoặc thông báo lỗi)
    response = client.recv(HEADER).decode(FORMAT)

    # Kiểm tra nếu server trả về thông báo lỗi
    if response == "File not found.":
        print("Bạn Không được tải file này! ")
        print("Nguyên nhân do bảo mật hoặc file không tồn tại")
        return

    # Nếu nhận được tên file hợp lệ, tiếp tục nhận kích thước file
    file_name = response
    file_size = int(client.recv(HEADER).decode(FORMAT))

    print(f"Đang tải xuống file: {file_name}, kích thước: {file_size} bytes")

    # Tạo thư mục client_data nếu chưa có
    if not os.path.exists('client_data'):
        os.makedirs('client_data')

    # Mở file và bắt đầu tải xuống
    with open(f"client_data/{file_name}", "wb") as file:
        total_received = 0
        
        download_button.config(state="disabled")
        download_window = Toplevel(root)
        download_window.title(f"Download file: \"{file_name}\"")
        
        download_label = Label(download_window, text=f"Đang tải xuống \"{file_name}\"...")
        download_label.pack(padx = 10, pady = 10)
        
        download_percent = Label(download_window,text="")
        download_percent.pack(padx = 10, pady = 10)
        
        progress = ttk.Progressbar(download_window,orient="horizontal",length=350, mode="determinate")
        progress.pack(padx = 10, pady = 10)
        progress["maximum"] = file_size
        try:
            while total_received < file_size:
                file_data = client.recv(1024)
                if not file_data:
                    break
                total_received += len(file_data)
                file.write(file_data)
                progress["value"] = total_received
                download_percent.config(text=f"{round((progress["value"] / progress['maximum']) * 100, 2)} %")
                download_window.update()

            if total_received == file_size:
                download_label.config(text = f"File \"{file_name}\" đã được tải xuống thành công.")
                print(f"File {file_name} đã được tải xuống thành công.")
            else:
                print(f"Lỗi: Chỉ nhận được {total_received} / {file_size} bytes.")

        except Exception as e:
            print(f"Lỗi khi tải file: {e}")
    download_button.config(state="normal")  



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


# Giao diện Tkinter
root = Tk()
root.title("File Upload/Download")
root.geometry("400x400")

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
    upload_button.grid(row=0, column=0, pady=10)
    download_button.grid(row=1, column=0, pady=10)
    close_button.grid(row=2, column=0, pady=10)
    
    # Ẩn các widget không cần thiết khi hiển thị file buttons
    login_button.grid_forget()
    register_button.grid_forget()
    username_label.grid_forget()
    password_label.grid_forget()
    username_entry.grid_forget()
    password_entry.grid_forget()
    show_hide_password_button.grid_forget()


# Trạng thái hiển thị của mật khẩu


def show_hide_password():
    if password_entry.cget("show") == "":  # Nếu đang hiển thị mật khẩu
        password_entry.config(show="*")   # Ẩn mật khẩu
        show_hide_password_button.config(text="Show")  # Đổi chữ trên nút
    else:
        password_entry.config(show="")    # Hiển thị mật khẩu
        show_hide_password_button.config(text="Hide")   # Đổi chữ trên nút

# Nút Upload


def on_upload_button_click():
    file_path = filedialog.askopenfilename(
        title="Chọn file để gửi")  # Chọn file từ máy tính
    if file_path:
        send_file(file_path)  # Gửi file đã chọn lên server
    else:
        print("Không có file nào được chọn.")

# Nút Download


def on_download_button_click():
    files = list_files()  # Lấy danh sách các file có sẵn từ server
    if files:
        # Cho phép người dùng chọn file bằng giao diện đồ họa
        file_to_download = filedialog.askopenfilename(
            title="Chọn file để tải xuống", initialdir="server_data\\PUBLIC", filetypes=[("All files", "*.*")])

        if file_to_download:
            # Chỉ lấy tên file, không cần đường dẫn đầy đủ
            file_to_download = file_to_download.split("/")[-1]
            download_file(file_to_download)  # Tải file đã chọn từ server
        else:
            print("Không có file nào được chọn.")


def close_connection():
    if client.fileno() != -1:  # Kiểm tra nếu socket vẫn còn hoạt động
        # Gửi tin nhắn ngắt kết nối đến server
        send_message(DISCONNECT_MESSAGE)
        client.close()  # Đóng kết nối
        print("Kết nối đã được đóng.")
    else:
        print("Kết nối đã bị đóng trước đó.")
    root.quit()  # Đóng cửa sổ Tkinter sau khi ngắt kết nối
    
def closing_window():
    # Hiển thị hộp thoại xác nhận 
    if messagebox.askokcancel("Thoát", "Bạn có muốn ngắt kết nối ??"):
        send_message(DISCONNECT_MESSAGE)
        client.close()  # Đóng kết nối
        root.destroy()  # Đóng cửa sổ

root.protocol("WM_DELETE_WINDOW", closing_window)

# Giao diện Đăng nhập / Đăng ký
username_label = Label(root, text="Username")
username_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
username_entry = Entry(root, textvariable=username_var)
username_entry.grid(row=0, column=1)

password_label = Label(root, text="Password")
password_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
password_entry = Entry(root, textvariable=password_var, show="*")
password_entry.grid(row=1, column=1)

show_hide_password_button = Button(root, text="Show", command=show_hide_password)
show_hide_password_button.grid(row=1, column=2, padx=5)

login_button = Button(root, text="Login", command=on_login_button_click,
                      bg="blue", fg="white", font=("Arial", 12))
login_button.grid(row=2, column=0, padx=5, pady=5)

register_button = Button(root, text="Register", command=on_register_button_click,
                         bg="green", fg="white", font=("Arial", 12))
register_button.grid(row=3, column=0, padx=5, pady=5)

# Nút Upload và Download chỉ hiển thị khi đăng nhập thành công
upload_button = Button(root, text="Upload File", command=on_upload_button_click,
                       bg="green", fg="white", font=("Arial", 12))
download_button = Button(root, text="Download File",
                         command=on_download_button_click, bg="blue", fg="white", font=("Arial", 12))

close_button = Button(root, text="Close Connection",
                      command=close_connection, bg="red", fg="white", font=("Arial", 12))

# Kết nối đến server
if not connect_to_server():
    root.quit()

root.mainloop()
