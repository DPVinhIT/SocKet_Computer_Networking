import socket
import threading
import os

# Constants
HEADER = 64
FORMAT = 'utf-8'
SERVER_DATA_DIR = "server_data"
PUBLIC_DIR = os.path.join(SERVER_DATA_DIR, "PUBLIC")
BUFFER_SIZE = 1024
SERVER = "0.0.0.0"
PORT = 12345
# Tạo thư mục 
os.makedirs(PUBLIC_DIR, exist_ok=True)

def handle_client(client_socket, address):
    """Handle incoming client connection."""
    print(f"Connection from {address} established.")
    try:
        with client_socket:
            # Nhận độ dài tên thư mục
            folder_name_length = int(client_socket.recv(HEADER).decode(FORMAT))
            folder_name = client_socket.recv(folder_name_length).decode(FORMAT)
            FOLDER_DIR = os.path.join(PUBLIC_DIR, folder_name)
            os.makedirs(FOLDER_DIR, exist_ok=True)
            file_name_length = int(client_socket.recv(HEADER).decode(FORMAT))
            file_name = client_socket.recv(file_name_length).decode(FORMAT)
            # Khởi tạo đường dẫn file
            file_path = os.path.join(FOLDER_DIR, file_name)

            # Nhận và lưu file
            with open(file_path, 'wb') as file:
                while data := client_socket.recv(BUFFER_SIZE):
                    file.write(data)

            print(f"File '{file_name}' from {address} saved to '{file_path}'.")

    except Exception as e:
        print(f"Error handling client {address}: {e}")

def upload_files_in_folder_parallel():
    """Start the server to accept file uploads."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        try:
            server.bind((SERVER, PORT))
            server.listen()
            print(f"Server is listening on {SERVER}:{PORT}...")

            while True:
                client_socket, addr = server.accept()
                thread = threading.Thread(target=handle_client, args=(client_socket, addr))
                thread.start()
                print(f"Active connections: {threading.active_count() - 1}")

        except Exception as e:
            print(f"Server error: {e}")

if __name__ == "__main__":
    upload_files_in_folder_parallel()
