import socket
import sys
import os
import threading

def send_all(sock, data):
    chunk_size = 1024  # Size of each chunk
    total_sent = 0
    while total_sent < len(data):
        end_index = min(total_sent + chunk_size, len(data))
        chunk = data[total_sent:end_index]
        sent = sock.send(chunk)
        if sent == 0:
            raise RuntimeError("Socket connection broken")
        total_sent += sent

def recv_all(sock, num_bytes):
    data = bytearray()
    total_received = 0
    while total_received < num_bytes:
        packet = sock.recv(min(1024, num_bytes - total_received))
        if not packet:
            return None  # Connection closed or error
        data.extend(packet)
        total_received += len(packet)
        sock.send(b"OK")  # Send acknowledgment after receiving each chunk
    return data


def client_handler(connection, address):
    control_socket = connection
    try:
        print(f"Connection from {address} has been established.")
        while True:
            command = control_socket.recv(1024).decode().strip()
            if not command:
                break  # Connection closed

            if command.lower().startswith('get') or command.lower().startswith('put') or command.lower() == 'ls':
                data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                data_socket.bind(('localhost', 0))
                data_port = data_socket.getsockname()[1]
                data_socket.listen(1)
                control_socket.send(str(data_port).encode())

                client_data_sock, _ = data_socket.accept()
                if command.lower().startswith('get'):
                    filename = command.split()[1]
                    try:
                        with open(filename, 'rb') as f:
                            content = f.read()
                        client_data_sock.sendall(str(len(content)).encode() + b' ')
                        send_all(client_data_sock, content)
                        print(f"SUCCESS: Sent '{filename}' ({len(content)} bytes)")
                    except FileNotFoundError:
                        client_data_sock.send(b"0 File not found")
                        print(f"FAILURE: File '{filename}' not found")

                elif command.lower().startswith('put'):
                    filename = command.split()[1]
                    file_size = int(client_data_sock.recv(1024).decode().strip())
                    data = recv_all(client_data_sock, file_size)
                    with open(filename, 'wb') as f:
                        f.write(data)
                    print(f"SUCCESS: Received '{filename}' ({file_size} bytes)")

                elif command.lower() == 'ls':
                    files = os.listdir('.')
                    files_list = '\n'.join(files).encode()
                    client_data_sock.sendall(files_list)
                    print(f"SUCCESS: Listed directory contents")

                client_data_sock.close()
                data_socket.close()

            elif command.lower() == 'quit':
                print("SUCCESS: Client disconnected safely")
                break

        control_socket.close()
    except Exception as e:
        print(f"FAILURE: Error handling client {address}: {e}")
    finally:
        control_socket.close()

def start_server(port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', port))
    server_socket.listen(5)
    print(f"Server listening on port {port}")

    try:
        while True:
            client_sock, addr = server_socket.accept()
            thread = threading.Thread(target=client_handler, args=(client_sock, addr))
            thread.start()
    except KeyboardInterrupt:
        print("Server is shutting down")
    finally:
        server_socket.close()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python serv.py <PORTNUMBER>")
        sys.exit(1)
    port_number = int(sys.argv[1])
    start_server(port_number)
