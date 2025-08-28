import os
import subprocess

import time
import socket


def trigger_hid(hidraw_path):
    if not os.path.exists(hidraw_path):
        print(f"HID device not found: {hidraw_path}")
        return

    try:
        subprocess.run(["printf", "\\xA0\\x01\\x01\\xA2"], stdout=open(hidraw_path, "wb"))
        time.sleep(0.3)
        subprocess.run(["printf", "\\xA0\\x01\\x00\\xA1"], stdout=open(hidraw_path, "wb"))

    except PermissionError:
        print(f"Permission denied while accessing {hidraw_path}. Try running with sudo.")
    except Exception as e:
        print(f"Unexpected error while accessing {hidraw_path}: {e}")


def handle_relay(relay_number):
    hidraw_path = f"/dev/hidraw{relay_number - 1}"
    trigger_hid(hidraw_path)


HOST = '0.0.0.0'
PORT = 9747

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        s.bind((HOST, PORT))
        s.listen()

        print(f"Server started. Listening on {HOST}:{PORT}...")

        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Connection established: {addr}")
                data = conn.recv(1024)
                if data:
                    try:
                        relay_number = int(data.decode())
                        print(f"Received relay number: {relay_number}")
                        handle_relay(relay_number)
                        conn.sendall(b"Relay toggled.")
                    except ValueError:
                        conn.sendall(b"Invalid relay number.")
                else:
                    print("No data received.")
except KeyboardInterrupt:
    print("Shutting down...")
finally:
    print("GPIO pins cleaned up.")
