import socket
import threading
import os
import zipfile
import time
# from tkinter import Tk, Button, filedialog, Label, Entry, StringVar, messagebox, ttk, Toplevel
from tkinter import*
from tkinter import ttk, Toplevel, messagebox, filedialog, StringVar
import tkinter.simpledialog as simpledialog
PORT = 12345
HEADER = 64
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
FILE_UPLOAD_FILE_MESSAGE = "!UPLOAD_FILE"
FILE_UPLOAD_FOLDER_MESSAGE="!UPLOAD_FOLDER"
FILE_LIST_REQUEST = "!LIST"
FILE_DOWNLOAD_REQUEST = "!DOWNLOAD"
REGISTER_REQUEST = "!REGISTER"
LOGIN_REQUEST = "!LOGIN"

#SERVER = "192.168.1.97"  # Địa chỉ IP của server
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

# Nút Upload Folder
def on_upload_folder_button_click():
    # Mở hộp thoại để chọn thư mục, với thư mục mặc định là client_data
    folder_path = filedialog.askdirectory(title="Chọn thư mục để gửi", initialdir="client_data")

    if folder_path:  # Người dùng đã chọn một thư mục
        # Kiểm tra xem thư mục có nằm trong thư mục client_data không
        if os.path.abspath(folder_path).startswith(os.path.abspath("client_data")):
            # Lấy tên của thư mục từ đường dẫn
            folder_name = get_folder_name(folder_path)
            
            # Gửi tên thư mục lên server trước
            send_message(folder_name)  # Giả định hàm này gửi tên folder lên server
            
            # Sau đó gửi toàn bộ file trong thư mục
            send_folder(folder_path)
            
            messagebox.showinfo("Server", f"Đã gửi thư mục {folder_name} lên server.")
        else:
            messagebox.showerror("Error", "Chỉ có thể chọn folder trong thư mục client_data.")
    else:  # Người dùng không chọn thư mục
        messagebox.showinfo("Thông báo", "Bạn chưa chọn thư mục nào.")

def send_file(file_path):
    send_message(f"{FILE_UPLOAD_FILE_MESSAGE} {file_path.split('/')[-1]}")
    file_length = os.path.getsize(file_path)
    with open(file_path, "rb") as file:

        send_length = str(file_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        client.send(send_length)
        while True: 
            file_data = file.read(1024)
            if not file_data:
                break
            client.send(file_data)

        
def handle_download(file_size):
    pass
        
def download_file(filename): 
    """
    Yêu cầu server gửi file về client, chỉ cho phép tải file từ thư mục PUBLIC
    """
    send_message(f"{FILE_DOWNLOAD_REQUEST} {filename}")

    # Nhận phản hồi đầu tiên từ server (tên file hoặc thông báo lỗi)
    response = client.recv(HEADER).decode(FORMAT)

    # Kiểm tra nếu server trả về thông báo lỗi
    if response == "File not found.":
        messagebox.askokcancel("Error", "Bạn Không được tải file này! Nguyên nhân do bảo mật hoặc file không tồn tại")
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
        download_window1 = Toplevel(root)
        download_window1.title(f"Download file: \"{file_name}\"")
        
        download_label = Label(download_window1, text=f"Đang tải xuống \"{file_name}\"...")
        download_label.pack(padx = 10, pady = 10)
        
        download_percent = Label(download_window1,text="")
        download_percent.pack(padx = 10, pady = 10)
        
        progress = ttk.Progressbar(download_window1,orient="horizontal",length=350, mode="determinate")
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
                download_window1.update()

            if total_received == file_size:
                download_label.config(text = f"File \"{file_name}\" đã được tải xuống thành công.")
                print(f"File {file_name} đã được tải xuống thành công.")
            else:
                print(f"Lỗi: Chỉ nhận được {total_received} / {file_size} bytes.")

        except Exception as e:
            print(f"Lỗi khi tải file: {e}")
    download_button.config(state="normal")  

def parse_folder_tree(data):
    """
    Chuyển đổi chuỗi nhận được từ server thành cấu trúc cây.
    """
    # Đánh giá chuỗi thành dict (cấu trúc cây)
    folder_tree = eval(data)  # Đổi chuỗi thành từ điển
    return folder_tree
def populate_tree(tree, parent, structure):
    """
    Thêm các node từ cấu trúc cây vào Treeview.
    """
    for name, children in structure.items():
        node_id = tree.insert(parent, "end", text=name, open=False)
        if children:
            populate_tree(tree, node_id, children)

def create_tree_view(folder_tree):
    """
    Tạo giao diện hiển thị Treeview từ cấu trúc cây.
    """
    tree_view = Toplevel(file_window)  # Tạo cửa sổ con cho Treeview
    tree_view.title("Folder Tree View")
    
    # Tạo Treeview
    tree = ttk.Treeview(tree_view)  # Lưu ý: tree nên được tạo trong tree_view chứ không phải root
    tree.heading("#0", text="Folders", anchor="w")
    tree.pack(fill="both", expand=True)

    # Thêm dữ liệu vào Treeview
    
    populate_tree(tree, "", folder_tree)

    def on_choose_button_click():
        selected_item = tree.selection()
        if selected_item:
            # Kiểm tra nếu node chọn là node lá
            if not tree.get_children(selected_item):  # Nếu không có phần tử con thì đây là node lá
                file_to_download = tree.item(selected_item, "text")  # Lấy tên thư mục được chọn
                download_file(file_to_download)
                tree_view.destroy()
            else:
                print("Bạn chỉ có thể chọn các node lá!")  # Thông báo nếu chọn node không phải là node lá

    # Nút chọn để lấy thư mục đã chọn
    choose_button = Button(tree_view, text="Chọn", command=on_choose_button_click)
    choose_button.pack(pady=10)

    # Cập nhật lại khi nhấp chuột
    tree.bind("<ButtonRelease-1>", lambda event: on_treeview_click(event=event, tree=tree))

def on_treeview_click(event, tree):
    selected_item = tree.selection()
    # Nếu đã chọn một mục, bỏ chọn mục cũ
    if len(selected_item) > 1:
        tree.selection_remove(selected_item[1:])  # Bỏ chọn các mục khác

# Gắn sự kiện để phát hiện khi người dùng chọn mục

def list_files():
    """
    Yêu cầu server gửi danh sách các file có sẵn để tải xuống hoặc upload
    """
    send_message(FILE_LIST_REQUEST)  # Yêu cầu server gửi danh sách file
    # Nhận danh sách các file từ server
    data = b""
    while True:
        packet = client.recv(1024)
        if packet == b"EOF":
            break
        data += packet
    
    return data.decode(FORMAT)

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

def send_folder(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            send_file(file_path)
            print(f"Đang gửi file: {file_name}")
            messagebox.showinfo("Upload", f"Đang gửi file: {file_name}")
    print(f"Tất cả các file trong thư mục {folder_path} đã được gửi.")
    messagebox.showinfo("Upload", f"Tất cả các file trong thư mục {folder_path} đã được gửi.")
def get_folder_name(folder_path):
    try:
        folder_name = os.path.basename(folder_path)
        return folder_name
    except Exception as e:
        print(f"Lỗi khi lấy tên thư mục: {e}")
        return None

def show_file_buttons():
    root.quit()
    root.destroy()
    global file_window 
    file_window =  Tk()
    file_window.title("Dowload\\Upload File")
    file_window.geometry("400x250")
    
    global download_button
    global upload_file_button
    global upload_folder_button
    
    # Nút Upload và Download chỉ hiển thị khi đăng nhập thành công
    upload_file_button = Button(file_window, text="Upload File", command=on_upload_button_click,
    bg="green", fg="white", font=("Arial", 12))
    
    upload_folder_button = Button(file_window, text="Upload Folder", command=on_upload_folder_button_click,
    bg="pink", fg="white", font=("Arial", 12))
    
    download_button = Button(file_window, text="Download File",
    command=on_download_button_click, bg="blue", fg="white", font=("Arial", 12))
    
    close_button = Button(file_window, text="Close Connection",
                      command=close_connection, bg="red", fg="white", font=("Arial", 12))
    upload_file_button.grid(row=0, column=0, pady=10)
    upload_folder_button.grid(row=1, column=0, pady=10)
    download_button.grid(row=2, column=0, pady=10)
    close_button.grid(row=3, column=0, pady=10)
    
    file_window.mainloop()

# Trạng thái hiển thị của mật khẩu
def show_hide_password():
    if show_password_var.get():  # Nếu checkbox được tích
        password_entry.config(show='')  # Hiển thị mật khẩu
    else:
        password_entry.config(show='*')  # Ẩn mật khẩu

# Nút Upload
def on_upload_button_click():
    file_path = filedialog.askopenfilename(
        title="Chọn file để gửi", initialdir="client_data")  # Chọn file từ máy tính

    if file_path:  # Người dùng đã chọn một file
        # Kiểm tra xem file có nằm trong thư mục client_data không
        if os.path.abspath(file_path).startswith(os.path.abspath("client_data")):
            send_file(file_path)  # Gửi file đã chọn lên server
            messagebox.showinfo("Server", f"Đã gửi file {os.path.basename(file_path)} lên server.")
        else:
            messagebox.showerror("Error", "Chỉ có thể chọn file trong thư mục client_data.")
    else:  # Người dùng không chọn file
        messagebox.showinfo("Thông báo", "Bạn chưa chọn file nào.")

# Nút Download
def on_download_button_click():
    data = list_files()
    folder_tree = parse_folder_tree(data)
    create_tree_view(folder_tree)

#Dừng kết nối 
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
        close_connection()
        root.destroy()  # Đóng cửa sổ

# Giao diện Tkinter
root = Tk()
root.title("File Upload/Download")
root.geometry("925x500+300+200")
root.configure(bg="#fff")
root.resizable(False,False)

username_var = StringVar()
password_var = StringVar()

img= PhotoImage(file = 'login.png')
image_login= Label(root,image=img,bg='white').place(x=50,y=50)

frame = Frame(root,width=350,height=350, bg='white')
frame.place(x=480,y=70)

heading = Label(frame,text='Sign in',fg='#57a1f8',bg='white',font=('Microsoft YaHei UI Light',23,'bold'))
heading.place(x=100,y=5)

# Nút tắt root
root.protocol("WM_DELETE_WINDOW", closing_window)

# Giao diện Đăng nhập / Đăng ký
def on_enter_user(event):
    if username_entry.get() == "Username":
        username_entry.delete(0,END)
def on_leave_user(event):
    name = username_entry.get()
    if name=='':
        username_entry.insert(0,'Username')

username_entry = Entry(frame, textvariable=username_var,width=25,fg='black',border=0,bg='white',font=('Microsoft YaHei UI Light',11))
username_entry.place(x=30,y=80)
username_entry.insert(0,'Username')
username_entry.bind('<FocusIn>',on_enter_user)
username_entry.bind('<FocusOut>',on_leave_user)

Frame(frame,width=295,height=2,bg='black').place(x=25,y=107)

def on_enter_pass(event):
    if password_entry.get() == "Password":
        password_entry.delete(0,END)
        password_entry.config(show="*")
def on_leave_pass(event):
    password = password_entry.get()
    if password=='':
        password_entry.insert(0,'Password')

password_entry = Entry(frame, textvariable=password_var,border=0,bg='white',font=('Microsoft YaHei UI Light',11))
password_entry.place(x=30,y=150)
password_entry.insert(0,'Password')
password_entry.bind('<FocusIn>',on_enter_pass)
password_entry.bind('<FocusOut>',on_leave_pass)

Frame(frame,width=295,height=2,bg='black').place(x=25,y=177)

Button(frame,text='Sign in',command=on_login_button_click,width=39,pady=7,bg='#57a1f8',fg='white',border=0).place(x=35,y=220)
Label(frame,text="Don't have an account?",fg='black',bg='white',font=('Microsoft YaHei UI Light',9)).place(x=75,y=270)

sign_up = Button(frame,text='Sign up',command=on_register_button_click,width=6,border=0,bg='white',cursor='hand2',fg='#57a1f8')
sign_up.place(x=215,y=270)

show_password_var = IntVar()  # Biến lưu trạng thái của checkbox (1 = tích, 0 = không tích)
show_password = Checkbutton(frame, variable=show_password_var, 
    onvalue=1,offvalue=0, command=show_hide_password,
    bg='white',fg='black',border=0
)
show_password.place(x=30, y=190)

Label(frame,text="Show password",fg='black',bg='white',font=('Microsoft YaHei UI Light',9)).place(x=50, y=190)

# Kết nối đến server
if not connect_to_server():
    root.quit()

root.mainloop()
