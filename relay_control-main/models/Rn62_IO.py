import socket


class Rn62IO:
    BINARY_COMMANDS = {
        1: bytes([99, 3, 3, 7, 7, 9, 9, 1, 1]),
        2: bytes([99, 3, 3, 7, 7, 9, 9, 2, 1]),
    }

    def trigger_relays(self, ip, port, relay_number=None, duration=None):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect((ip, port))
            if relay_number is not None:
                command_to_send = self.BINARY_COMMANDS[relay_number]
            else:
                commands = [self.BINARY_COMMANDS[key] for key in self.BINARY_COMMANDS]
                command_to_send = b''.join(commands)

            client.sendall(command_to_send)
            print(f"RN-62 Binary command sent: {command_to_send.hex()}")

            data = client.recv(1024)
            print(f"Received data: {data.hex()}")
            return True
