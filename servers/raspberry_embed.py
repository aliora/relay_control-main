import os
import subprocess
import time
import socket
import glob

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


def trigger_gpio(relay_pin, relay_number=None, duration=0.3):
    """Toggle a GPIO relay for `duration` seconds."""
    GPIO.setup(relay_pin, GPIO.OUT)
    GPIO.output(relay_pin, GPIO.HIGH)
    if relay_number is None:
        print(f"Toggling GPIO {relay_pin}...")
    else:
        print(f"Toggling relay {relay_number} (GPIO {relay_pin})...")
    time.sleep(duration)
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


def trigger_hid(hidraw_path, duration=0.3):
    candidates = []
    if os.path.exists(hidraw_path):
        candidates.append(hidraw_path)
    # Add common device paths
    candidates.extend(sorted(glob.glob('/dev/hidraw*')))
    candidates.extend(sorted(glob.glob('/dev/ttyUSB*')))
    candidates.extend(sorted(glob.glob('/dev/serial/by-id/*')))

    # Remove duplicates while preserving order
    seen = set()
    devices = []
    for p in candidates:
        if p not in seen:
            seen.add(p)
            devices.append(p)

    if not devices:
        print(f"HID device not found: {hidraw_path} and no candidates")
        return

    # Try each candidate until one works
    for dev in devices:
        try:
            # Attempt raw write (open in binary mode)
            cmd_on = b"\xA0\x01\x01\xA2"
            cmd_off = b"\xA0\x01\x00\xA1"
            with open(dev, 'wb') as f:
                f.write(cmd_on)
                f.flush()
                os.fsync(f.fileno())
            print(f"Usb Relay Opened (via {dev})")
            time.sleep(duration)
            with open(dev, 'wb') as f:
                f.write(cmd_off)
                f.flush()
                os.fsync(f.fileno())
            print(f"Usb Relay Closed (via {dev})")
            return
        except PermissionError:
            print(f"Permission denied while accessing {dev}. Try running with sudo or adjust udev rules.")
            # try next candidate
        except FileNotFoundError:
            # device disappeared, try next
            continue
        except Exception as e:
            print(f"Unexpected error while accessing {dev}: {e}")
            # try next

    print(f"All candidate devices tried and failed for requested path: {hidraw_path}")


def handle_relay(relay_number, duration_ms=None):
    """Handle relay toggle. duration_ms is optional in milliseconds."""
    if relay_number not in relay_pins:
        print(f"Invalid relay number: {relay_number}")
        return

    gpio_pin = relay_pins[relay_number][0]
    hidraw_path = relay_pins[relay_number][1]
    # convert milliseconds to seconds (fallback to default 300ms)
    if duration_ms is None:
        duration = 0.3
    else:
        try:
            duration = float(duration_ms) / 1000.0
        except Exception:
            duration = 0.3

    trigger_gpio(gpio_pin, relay_number, duration=duration)
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
                            relay_number = int(parts[0])
                            duration_ms = int(parts[1]) if parts[1] else None
                        else:
                            relay_number = int(decoded)
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
    GPIO.cleanup()
    print("GPIO pins cleaned up.")