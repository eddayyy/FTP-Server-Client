import socket
import sys

def send_all(sock, data):
    chunk_size = 1024
    total_sent = 0
    while total_sent < len(data):
        end_index = min(total_sent + chunk_size, len(data))
        chunk = data[total_sent:end_index]
        sent = sock.send(chunk)
        if sent == 0:
            raise RuntimeError("Socket connection broken")
        ack = sock.recv(2)  # Wait for acknowledgment from the server
        if ack == b'OK':
            print(f"ACK received for {total_sent + sent}/{len(data)} bytes")  # Print acknowledgment message
        total_sent += sent


def recv_all(sock, num_bytes):
    data = bytearray()
    while len(data) < num_bytes:
        packet = sock.recv(min(1024, num_bytes - len(data)))
        if not packet:
            return None  # Connection closed or error
        data.extend(packet)
    return data

def data_transfer_connection(port):
    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.connect(('localhost', port))
    return data_socket

def main(server, port):
    menu = '''
        \033[95mls\033[0m: \033[94mList files in the server\033[0m
        \033[95mget\033[0m: \033[94mDownload file from server (ex: get file.txt)\033[0m
        \033[95mput\033[0m: \033[94mUpload file to server (ex: put file.txt)\033[0m
        \033[95mquit\033[0m: \033[94mStop server\033[0m
        '''
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server, port))
    print(f'Control connection established with SERVER at {server} PORT {port}')
    print('Welcome to FTP. Use the following commands:')
    print(menu)

    while True:
        command = input("ftp> ").strip()
        if command.lower() == 'quit':
            print("Session ended.")
            client_socket.send(command.encode())
            break
        client_socket.send(command.encode())

        if command.lower().startswith('get') or command.lower().startswith('put'):
            data_port = int(client_socket.recv(1024).decode().strip())  # Receive data port from server
            data_socket = data_transfer_connection(data_port)
            if command.lower().startswith('get'):
                file_size = int(data_socket.recv(1024).decode().strip())
                if file_size > 0:
                    data = recv_all(data_socket, file_size)
                    filename = command.split()[1]
                    with open(filename, 'wb') as f:
                        f.write(data)
                    print(f"Successfully received '{filename}' ({file_size} bytes)")
                else:
                    print("File not found.")
            elif command.lower().startswith('put'):
                filename = command.split()[1]
                try:
                    with open(filename, 'rb') as f:
                        data = f.read()
                    data_socket.send(str(len(data)).encode() + b' ')
                    send_all(data_socket, data)
                except FileNotFoundError:
                    print(f"File not found: {filename}")
                except Exception as e:
                    print(f"Failed to send file: {e}")
            data_socket.close()
        elif command.lower() == 'ls':
            data_port = int(client_socket.recv(1024).decode().strip())
            data_socket = data_transfer_connection(data_port)
            data = data_socket.recv(1024)
            print(data.decode())
            data_socket.close()

    client_socket.close()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python cli.py <server machine> <server port>")
        sys.exit(1)
    server_machine = sys.argv[1]
    server_port = int(sys.argv[2])
    main(server_machine, server_port)
