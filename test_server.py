import socket


class TestServer:
    def __init__(self, ip='0.0.0.0', port=5050):
        self.ip = ip
        self.port = port

    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind((self.ip, self.port))
            server.listen(1)
            print(f"Server listening on {self.ip}:{self.port}")

            while True:
                client_socket, client_address = server.accept()
                with client_socket:
                    print(f"Connected by {client_address}")
                    data = client_socket.recv(1024).decode('ascii')
                    print(f"Received data: {data}")

                    if data:
                        response = "Command received successfully"
                        client_socket.sendall(response.encode('ascii'))

test_server = TestServer()
test_server.start_server()
