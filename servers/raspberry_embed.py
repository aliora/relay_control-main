import os
import subprocess
import time
import socket

# Try import RPi.GPIO, fall back to a fake implementation for testing on non-RPi
try:
    from RPi import GPIO
    IS_RPI = True
except Exception:
    IS_RPI = False
    class _FakeGPIO:
        BOARD = 'BOARD'
        OUT = 'OUT'
        HIGH = 1
        LOW = 0

        def setmode(self, mode):
            print(f"[fakeGPIO] setmode({mode})")

        def setup(self, pin, mode):
            print(f"[fakeGPIO] setup(pin={pin}, mode={mode})")

        def output(self, pin, val):
            print(f"[fakeGPIO] output(pin={pin}, val={val})")

        def cleanup(self, pin=None):
            print(f"[fakeGPIO] cleanup(pin={pin})")

    GPIO = _FakeGPIO()

relay_pins = {
    1: [16, "/dev/hidraw0"],
    2: [18, "/dev/hidraw1"]
}

GPIO.setmode(GPIO.BOARD)


def trigger_gpio(relay_pin, relay_number=None):
    GPIO.setup(relay_pin, GPIO.OUT)
    GPIO.output(relay_pin, GPIO.HIGH)
    if relay_number is None:
        print(f"Toggling GPIO {relay_pin}...")
    else:
        print(f"Toggling relay {relay_number} (GPIO {relay_pin})...")
    time.sleep(0.3)
    GPIO.output(relay_pin, GPIO.LOW)
    if relay_number is None:
        print(f"GPIO {relay_pin} turned off.")
    else:
        print(f"Relay {relay_number} turned off.")
    # cleanup specific channel
    try:
        GPIO.cleanup(relay_pin)
    except Exception:
        # ignore cleanup errors
        pass


def trigger_hid(hidraw_path):
    if not os.path.exists(hidraw_path):
        print(f"HID device not found: {hidraw_path}")
        return

    try:
        subprocess.run(["printf", "\\xA0\\x01\\x01\\xA2"], stdout=open(hidraw_path, "wb"))
        print("Usb Relay Opened")
        time.sleep(0.3)
        subprocess.run(["printf", "\\xA0\\x01\\x00\\xA1"], stdout=open(hidraw_path, "wb"))
        print("Usb Relay Closed")

    except PermissionError:
        print(f"Permission denied while accessing {hidraw_path}. Try running with sudo.")
    except Exception as e:
        print(f"Unexpected error while accessing {hidraw_path}: {e}")


def handle_relay(relay_number):
    if relay_number not in relay_pins:
        print(f"Invalid relay number: {relay_number}")
        return

    gpio_pin = relay_pins[relay_number][0]
    hidraw_path = relay_pins[relay_number][1]
    trigger_gpio(gpio_pin, relay_number)
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
    GPIO.cleanup()
    print("GPIO pins cleaned up.")