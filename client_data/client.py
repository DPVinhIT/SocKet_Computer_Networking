import socket
import os
# from tkinter import Tk, Button, filedialog, Label, Entry, StringVar, messagebox, ttk, Toplevel
from tkinter import*
from tkinter import ttk, Toplevel, messagebox, filedialog, StringVar
import tkinter.simpledialog as simpledialog
import time
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

folder_path = "client_data"
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

##################################################################################################################################
# Đăng nhập
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

# Trạng thái hiển thị của mật khẩu
def show_hide_password():
    if show_password_var.get():  # Nếu checkbox được tích
        password_entry.config(show='')  # Hiển thị mật khẩu
    else:
        password_entry.config(show='*')  # Ẩn mật khẩu

##################################################################################################################################
# KẾT NỐI
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
    root.destroy()
     
def closing_window():
    # Hiển thị hộp thoại xác nhận 
    if messagebox.askokcancel("Thoát", "Bạn có muốn ngắt kết nối ??"):
        close_connection()
        root.quit()
        root.destroy()  # Đóng cửa sổ

def close_connection_file_window():
    if client.fileno() != -1:  # Kiểm tra nếu socket vẫn còn hoạt động
        # Gửi tin nhắn ngắt kết nối đến server
        send_message(DISCONNECT_MESSAGE)
        client.close()  # Đóng kết nối
        print("Kết nối đã được đóng.")
    else:
        print("Kết nối đã bị đóng trước đó.")
    file_window.quit()  # Đóng cửa sổ Tkinter sau khi ngắt kết nối
    file_window.destroy()
    
def closing_file_window():
    # Hiển thị hộp thoại xác nhận 
    if messagebox.askokcancel("Thoát", "Bạn có muốn ngắt kết nối ??"):
        close_connection_file_window()
        file_window.quit()
        file_window.destroy()  # Đóng cửa sổ
##################################################################################################################################
# DOWNLOAD 

# Nút Download
def on_download_button_click():
    data = list_files()
    folder_tree = parse_folder_tree(data)
    create_tree_view(folder_tree)
    
# Nút Upload Folder
def list_files():
    """
    Yêu cầu server gửi danh sách các file có sẵn để tải xuống hoặc upload
    """
    send_message(FILE_LIST_REQUEST)  # Yêu cầu server gửi danh sách file
    # Nhận danh sách các file từ server
    data = ""
    while True:
        packet = client.recv(1024).decode(FORMAT)
        if not packet :
            break
        data += packet
        if "EOF" in packet:
            data = data.replace("EOF","")
            break
    return data

def download_file(filename, tree_view):
    """
    Yêu cầu server gửi file về client, chỉ cho phép tải file từ thư mục PUBLIC
    """
    try:
        send_message(f"{FILE_DOWNLOAD_REQUEST} {filename}")

        # Nhận phản hồi đầu tiên từ server (tên file hoặc thông báo lỗi)
        response = client.recv(HEADER).decode(FORMAT)

        # Kiểm tra nếu server trả về thông báo lỗi
        if response == "File not found.":
            messagebox.askokcancel("Error", "Bạn không được tải file này! Nguyên nhân do bảo mật hoặc file không tồn tại")
            return

        # Nếu nhận được tên file hợp lệ, tiếp tục nhận kích thước file
        file_name = response.split("/")[-1]
        file_size = int(client.recv(HEADER).decode(FORMAT))

        download_window1 = Toplevel(tree_view)
        download_window1.title(f"Download file: \"{file_name}\"")
        
        download_label = Label(download_window1, text=f"Đang tải xuống \"{file_name}\"...")
        download_label.pack(padx=10, pady=10)
        
        download_percent = Label(download_window1, text="")
        download_percent.pack(padx=10, pady=10)
        
        progress = ttk.Progressbar(download_window1, orient="horizontal", length=350, mode="determinate")
        progress.pack(padx=10, pady=10)
        progress["maximum"] = file_size

        # Biến điều khiển Pause, Resume, và Cancel
        is_paused = [False]
        is_cancelled = [False]

        def toggle_pause_resume():
            if is_paused[0]:
                is_paused[0] = False
                pause_resume_button.config(text="Pause", command=toggle_pause_resume)
            else:
                is_paused[0] = True
                pause_resume_button.config(text="Resume", command=toggle_pause_resume)

        def cancel_download():
            # Hiển thị hộp thoại xác nhận
            confirm = messagebox.askyesno("Xác nhận hủy", f"Bạn có chắc chắn muốn hủy tải file \"{file_name}\" không?")
            if confirm:
                is_cancelled[0] = True
                download_label.config(text=f"Đang hủy tải file \"{file_name}\"...")
                messagebox.showinfo("Thông báo", f"Đã hủy tải file \"{file_name}\".") 

        # Thêm nút Pause/Resume và Cancel
        button_frame = Frame(download_window1)
        button_frame.pack(pady=10)

        pause_resume_button = Button(button_frame, text="Pause", command=toggle_pause_resume)
        pause_resume_button.pack(side="left", padx=10)

        cancel_button = Button(button_frame, text="Cancel", command=cancel_download)
        cancel_button.pack(side="left", padx=10)

        print(f"Đang tải xuống file: {file_name}, kích thước: {file_size} bytes")

        # Tạo thư mục client_data nếu chưa có
        if not os.path.exists('client_data'):
            os.makedirs('client_data')

        # Kiểm tra và đổi tên tệp nếu trùng
        base_name, extension = os.path.splitext(file_name)
        counter = 1
        while os.path.exists(os.path.join('client_data', file_name)):
            file_name = f"{base_name}({counter}){extension}"
            counter += 1

        # Mở file và bắt đầu tải xuống
        file_path = os.path.join('client_data', file_name)  # Đường dẫn đầy đủ của file
        with open(file_path, "wb") as file:
            total_received = 0
            try:
                while total_received < file_size:
                    if is_cancelled[0]:  # Kiểm tra nếu người dùng hủy tải
                        file.close()  # Đóng file đang mở
                        if os.path.exists(file_path):  # Kiểm tra và xóa file
                            os.remove(file_path)
                        download_label.config(text=f"Đã hủy tải file \"{file_name}\".")
                        print(f"File \"{file_name}\" đã bị hủy và xóa.")
                        return

                    while is_paused[0]:  # Tạm dừng nếu trạng thái Pause
                        download_window1.update()
                        time.sleep(0.1)

                    file_data = client.recv(1024)
                    if not file_data:
                        break
                    total_received += len(file_data)
                    file.write(file_data)
                    progress["value"] = total_received
                    download_percent.config(text=f"{round((progress['value'] / progress['maximum']) * 100, 2)} %")
                    download_window1.update()
                if total_received == file_size:
                    download_label.config(text=f"File \"{file_name}\" đã được tải xuống thành công.")
                    print(f"File {file_name} đã được tải xuống thành công.")
                else:
                    print(f"Lỗi: Chỉ nhận được {total_received} / {file_size} bytes.")
                    if os.path.exists(file_path):  # Xóa file nếu tải không đủ
                        os.remove(file_path)
            except Exception as e:
                if os.path.exists(file_path):  # Xóa file nếu có lỗi xảy ra
                    os.remove(file_path)
                print(f"Lỗi khi tải file: {e}")
    except Exception as e:
        print(f"Lỗi {e}")



        
# def parse_folder_tree(data):
#     """
#     Chuyển đổi chuỗi nhận được từ server thành cấu trúc cây.
#     """
#     # Đánh giá chuỗi thành dict (cấu trúc cây)
#     folder_tree = eval(data)  # Đổi chuỗi thành từ điển
#     return folder_tree

import ast

def parse_folder_tree(data):
    """
    Chuyển đổi chuỗi nhận được từ server thành cấu trúc cây.
    """
    try:
        # Kiểm tra nếu dữ liệu có dấu "Invalid command"
        if "Invalid command" in data:
            raise ValueError("Dữ liệu nhận được từ server không hợp lệ.")
        
        # Sử dụng ast.literal_eval() thay vì eval()
        folder_tree = ast.literal_eval(data)  # An toàn hơn so với eval
        return folder_tree
    except Exception as e:
        print(f"Lỗi khi phân tích dữ liệu: {e}")
        return {}  # Trả về một từ điển rỗng nếu có lỗi


def populate_tree(tree, parent, structure):
    """
    Thêm các node từ cấu trúc cây vào Treeview.
    """
    for name, children in structure.items():
        node_id = tree.insert(parent, "end", text=name, open=False)
        if children:
            populate_tree(tree, node_id, children)

def find_path(tree, target, current_path=""):
    for key, value in tree.items():
        # Cập nhật đường dẫn hiện tại
        new_path = f"{current_path}/{key}" if current_path else key
        
        # Kiểm tra nếu key là file (value == None)
        if key == target and value is None:
            return new_path
        
        # Nếu value là folder con (dạng dict), tiếp tục đệ quy
        if isinstance(value, dict):
            result = find_path(value, target, new_path)
            if result:  # Nếu tìm thấy trong nhánh con, trả về kết quả
                return result
    
    # Không tìm thấy trong nhánh này
    return None

def create_tree_view(folder_tree):
    """
    Tạo giao diện hiển thị Treeview từ cấu trúc cây.
    """
    download_button.config(state="disabled")
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
                file_path = find_path(folder_tree, file_to_download, "")
                download_file(file_path, tree_view)  # Gọi hàm tải file
                # Đóng cửa sổ tree_view sau khi chọn file và tải xuống
                tree_view.destroy()  # Đóng cửa sổ tree_view
                download_button.config(state="normal")
            else:
                messagebox.showwarning("Warning", "Bạn chỉ có thể chọn file, không phải folder!")

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

##################################################################################################################################
# UPLOAD FILE
def send_file(file_path):
    send_message(f"{FILE_UPLOAD_FILE_MESSAGE} {file_path.split('/')[-1]}")
    file_length = os.path.getsize(file_path)
    send_length = str(file_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    with open(file_path, "rb") as file:
        while True: 
            file_data = file.read(1024)
            if not file_data:
                break
            client.send(file_data)

##################################################################################################################################
#UPLOAD FOLDER
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
            
            # Gửi số lượng file trong thư mục
            send_message(str(len([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])))

            # Sau đó gửi toàn bộ file trong thư mục
            send_folder(folder_path)
            
            messagebox.showinfo("Server", f"Đã gửi thư mục {folder_name} lên server.")
        else:
            messagebox.showerror("Error", "Chỉ có thể chọn folder trong thư mục client_data.")
    else:  # Người dùng không chọn thư mục
        messagebox.showinfo("Thông báo", "Bạn chưa chọn thư mục nào.")

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

##################################################################################################################################
# Xử lí

##################################################################################################################################
# Giao diện
def show_file_buttons():
    root.quit()
    root.destroy()
    global file_window 
    file_window =  Tk()
    file_window.title("Download\\Upload File")
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
                      command=close_connection_file_window, bg="red", fg="white", font=("Arial", 12))
    
    upload_file_button.grid(row=0, column=0, pady=10)
    upload_folder_button.grid(row=1, column=0, pady=10)
    download_button.grid(row=2, column=0, pady=10)
    close_button.grid(row=3, column=0, pady=10)
    file_window.mainloop()
##################################################################################################################################

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
