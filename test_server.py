import socket
import json


class TestServer:
    def __init__(self, ip='0.0.0.0', port=5050, forward_ip='127.0.0.1', forward_port=9747):
        self.ip = ip
        self.port = port
        self.forward_ip = forward_ip
        self.forward_port = forward_port

    def _extract_http_body(self, data_str: str) -> str:
        # Split headers and body by the first blank line
        parts = data_str.split('\r\n\r\n', 1)
        if len(parts) == 2:
            return parts[1]
        # Some clients may send only LF
        parts = data_str.split('\n\n', 1)
        if len(parts) == 2:
            return parts[1]
        return ''

    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.ip, self.port))
            server.listen(5)
            print(f"Server listening on {self.ip}:{self.port}")

            while True:
                client_socket, client_address = server.accept()
                with client_socket:
                    print(f"Connected by {client_address}")
                    data = client_socket.recv(8192)
                    if not data:
                        continue
                    try:
                        data_str = data.decode('utf-8', errors='replace')
                        print(f"Received data: {data_str}")

                        body = self._extract_http_body(data_str)
                        if not body:
                            # No HTTP body: respond and continue
                            resp = 'HTTP/1.1 400 Bad Request\r\nContent-Length: 11\r\n\r\nBad Request'
                            client_socket.sendall(resp.encode('ascii'))
                            continue

                        # Try parse JSON from body
                        try:
                            payload = json.loads(body.strip())
                        except json.JSONDecodeError:
                            # Sometimes body may be preceded by extra lines; try to find first { ... }
                            start = body.find('{')
                            end = body.rfind('}')
                            if start != -1 and end != -1 and end > start:
                                try:
                                    payload = json.loads(body[start:end+1])
                                except Exception:
                                    payload = None
                            else:
                                payload = None

                        if not payload or 'relayNumber' not in payload:
                            resp = 'HTTP/1.1 400 Bad Request\r\nContent-Length: 21\r\n\r\n{"error":"no relayNumber"}'
                            client_socket.sendall(resp.encode('ascii'))
                            continue

                        # Relay number may be string or number
                        try:
                            relay_number = int(payload['relayNumber'])
                        except Exception:
                            relay_number = int(str(payload['relayNumber']))

                        print(f"Parsed relayNumber: {relay_number}")

                        # Forward plain relay number to local raspberry_embed server
                        try:
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as forward_sock:
                                forward_sock.connect((self.forward_ip, self.forward_port))
                                forward_sock.sendall(str(relay_number).encode('ascii'))
                            forwarded = True
                            print(f"Forwarded relay {relay_number} to {self.forward_ip}:{self.forward_port}")
                        except Exception as e:
                            forwarded = False
                            print(f"Failed to forward to relay server: {e}")

                        # Send HTTP response back
                        if forwarded:
                            body_resp = json.dumps({"status": "ok", "relay": relay_number})
                            resp = f'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(body_resp)}\r\n\r\n{body_resp}'
                        else:
                            body_resp = json.dumps({"status": "error", "message": "forward failed"})
                            resp = f'HTTP/1.1 502 Bad Gateway\r\nContent-Type: application/json\r\nContent-Length: {len(body_resp)}\r\n\r\n{body_resp}'

                        client_socket.sendall(resp.encode('utf-8'))

                    except Exception as e:
                        print(f"Error handling client: {e}")


test_server = TestServer()
test_server.start_server()
