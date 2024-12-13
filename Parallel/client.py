import socket
import threading
import os
import tkinter as tk
from tkinter import ttk

# Constants
HEADER = 64
FORMAT = 'utf-8'
BUFFER_SIZE = 1024
SERVER = socket.gethostbyname(socket.gethostname())
PORT = 12345

def send_file_parallel(filename, folder_name, folder_path, progress_var, percent_label):
    """Send a file to the server."""
    try:
        file_path = os.path.join(folder_path, filename)
        if not os.path.exists(file_path):
            print(f"File '{filename}' does not exist.")
            return

        file_size = os.path.getsize(file_path)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((SERVER, PORT))

            # Gửi tên thư mục và tên file
            folder_name_encoded = folder_name.encode(FORMAT)
            folder_name_length = len(folder_name_encoded)
            client_socket.send(f"{folder_name_length:<{HEADER}}".encode(FORMAT))
            client_socket.send(folder_name_encoded)

            # Gửi độ dài tên file và tên file
            filename_encoded = filename.encode(FORMAT)
            filename_length = len(filename_encoded)
            client_socket.send(f"{filename_length:<{HEADER}}".encode(FORMAT))
            client_socket.send(filename_encoded)

            # Gửi nội dung tệp trong từng gói tin nhỏ
            sent_bytes = 0
            with open(file_path, 'rb') as file:
                while chunk := file.read(BUFFER_SIZE):
                    client_socket.send(chunk)
                    sent_bytes += len(chunk)

                    # Cập nhật thanh tiến trình
                    progress = int((sent_bytes / file_size) * 100)
                    progress_var.set(progress)
                    percent_label.config(text=f"{progress}%")

            print(f"'{filename}' sent successfully.")
    except Exception as e:
        print(f"Failed to send '{filename}': {e}")


def get_file_list(folder_path):
    """Get a list of files in the specified folder."""
    if not os.path.exists(folder_path):
        print(f"Folder '{folder_path}' does not exist.")
        return []
    return [file for file in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, file))]


def upload_files_in_folder_with_gui(folder_path):
    """Upload files with a progress bar GUI."""
    folder_name = os.path.basename(folder_path)
    files = get_file_list(folder_path)
    if not files:
        print("No files found to upload.")
        return

    root = tk.Tk()
    root.title("File Upload Progress")
    root.geometry("600x400")

    tk.Label(root, text="Uploading Files:", font=("Arial", 14)).pack(pady=10)
    frame = tk.Frame(root)
    frame.pack(fill="both", expand=True, pady=10)

    progress_vars = []
    percent_labels = []

    for filename in files:
        file_label = tk.Label(frame, text=filename, anchor="w")
        file_label.pack(fill="x", padx=10)

        progress_var = tk.IntVar()
        progress_bar = ttk.Progressbar(frame, maximum=100, variable=progress_var)
        progress_bar.pack(fill="x", padx=10, pady=5)

        percent_label = tk.Label(frame, text="0%", width=5, anchor="e")
        percent_label.pack(anchor="e", padx=10)

        progress_vars.append(progress_var)
        percent_labels.append(percent_label)

    threads = []
    for index, filename in enumerate(files):
        thread = threading.Thread(
            target=send_file_parallel,
            args=(
                filename,
                folder_name,
                folder_path,
                progress_vars[index],
                percent_labels[index],
            ),
        )
        thread.start()
        threads.append(thread)

    def check_threads():
        if all(not thread.is_alive() for thread in threads):
            tk.Label(root, text="All files uploaded successfully!", font=("Arial", 12), fg="green").pack(pady=10)
        else:
            root.after(100, check_threads)

    check_threads()
    root.mainloop()


if __name__ == "__main__":
    folder_path = input("Enter the path of the folder to upload: ").strip()
    folder_path = folder_path.replace("\\", "/")

    if not os.path.isdir(folder_path):
        print("The specified path is not a valid folder.")
    else:
        upload_files_in_folder_with_gui(folder_path)
