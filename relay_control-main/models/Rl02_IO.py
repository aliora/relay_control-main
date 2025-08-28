import socket


class Rl02IO:
    RELAY_COUNT = 16
    RELAY_BEGIN_COMMAND = '<RL_BEGIN>'
    RELAY_END_COMMAND = '</RL_END>'
    RELAY_COMMANDS = [
        '<RL0>', '<RL1>', '<RL2>', '<RL3>', '<RL4>', '<RL5>', '<RL6>', '<RL7>',
        '<RL8>', '<RL9>', '<RL10>', '<RL11>', '<RL12>', '<RL13>', '<RL14>', '<RL15>'
    ]

    def trigger_relays(self, ip, port, relay_number=None, duration=None):
        commands_to_send = [self.RELAY_BEGIN_COMMAND]

        if relay_number is not None:
            if relay_number < 0 or relay_number >= self.RELAY_COUNT:
                raise ValueError("Invalid relay number")
            command = self.RELAY_COMMANDS[relay_number] + str(duration) + self.RELAY_COMMANDS[relay_number].replace('<',
                                                                                                                    '</')
            commands_to_send.append(command)
        else:
            for i in range(self.RELAY_COUNT):
                command = self.RELAY_COMMANDS[i] + str(duration) + self.RELAY_COMMANDS[i].replace('<', '</')
                commands_to_send.append(command)

        commands_to_send.append(self.RELAY_END_COMMAND)
        data_to_send = ''.join(commands_to_send)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect((ip, port))
            client.sendall(data_to_send.encode('ascii'))
            print(f"RL-02 ASCII command sent: {data_to_send}")

            data = client.recv(1024)
            print(f"Received data: {data.decode()}")
            return True
