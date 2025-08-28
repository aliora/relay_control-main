import socket


class RaspberryEmbed:
    def trigger_relays(self, ip, port, relay_number=None, duration=None):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect((ip, port))
            if relay_number is not None:
                client.sendall(str(relay_number).encode())
                print(f"Relay triggered: relay number {relay_number}")

                data = client.recv(1024)
                print(f"Response: {data.decode()}")
            else:
                print("No relay number provided.")
            return True
