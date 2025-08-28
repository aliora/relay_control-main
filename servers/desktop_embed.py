import os
import subprocess

import time
import socket


def trigger_hid(hidraw_path, duration=0.3):
    """Send ON then OFF commands to the HID device, waiting `duration` seconds between."""
    if not os.path.exists(hidraw_path):
        print(f"HID device not found: {hidraw_path}")
        return

    try:
        # ON
        subprocess.run(["printf", "\\xA0\\x01\\x01\\xA2"], stdout=open(hidraw_path, "wb"))
        time.sleep(duration)
        # OFF
        subprocess.run(["printf", "\\xA0\\x01\\x00\\xA1"], stdout=open(hidraw_path, "wb"))

    except PermissionError:
        print(f"Permission denied while accessing {hidraw_path}. Try running with sudo.")
    except Exception as e:
        print(f"Unexpected error while accessing {hidraw_path}: {e}")


def handle_relay(relay_number, duration_ms=None):
    """Map relay_number -> hidraw device and trigger it. duration_ms optional in milliseconds."""
    try:
        relay_number = int(relay_number)
    except Exception:
        print(f"Invalid relay number passed to handler: {relay_number}")
        return

    # map relay 1 -> /dev/hidraw0, relay 2 -> /dev/hidraw1, etc.
    hidraw_path = f"/dev/hidraw{relay_number - 1}"

    if duration_ms is None:
        duration = 0.3
    else:
        try:
            duration = float(duration_ms) / 1000.0
        except Exception:
            duration = 0.3

    trigger_hid(hidraw_path, duration=duration)


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
                        decoded = data.decode().strip()
                        # support optional duration: "<relay>" or "<relay>,<ms>"
                        if ',' in decoded:
                            parts = decoded.split(',')
                            relay_number = parts[0]
                            duration_ms = parts[1] if parts[1] else None
                        else:
                            relay_number = decoded
                            duration_ms = None

                        print(f"Received relay number: {relay_number}, duration_ms={duration_ms}")
                        handle_relay(relay_number, duration_ms=duration_ms)
                        conn.sendall(b"Relay toggled.")
                    except ValueError:
                        conn.sendall(b"Invalid relay number or duration.")
                else:
                    print("No data received.")
except KeyboardInterrupt:
    print("Shutting down...")
finally:
    print("Server exiting.")
