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
    print(f"🔌 Starting HID relay control for {hidraw_path} (duration: {duration}s)")
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
        print(f"❌ HID device not found: {hidraw_path} and no candidates")
        return

    print(f"📋 Found {len(devices)} candidate devices: {devices}")

    # Different command sets for different relay types
    command_sets = [
        # Standard USB relay commands (most common)
        {
            'on': b'\xA0\x01\x01\xA2',
            'off': b'\xA0\x01\x00\xA1'
        },
        # Alternative relay commands with different checksum
        {
            'on': b'\xA0\x01\x01',
            'off': b'\xA0\x01\x00'
        },
        # LCUS-1 type relay commands
        {
            'on': b'\xFF\x01\x01',
            'off': b'\xFF\x01\x00'
        },
        # Simple 1-channel relay commands
        {
            'on': b'\x01',
            'off': b'\x00'
        },
        # Another common format
        {
            'on': b'\xFE\x05\x00\x00\xFF\x00\x98\x35',
            'off': b'\xFE\x05\x00\x00\x00\x00\xD9\xC5'
        }
    ]

    # Try each device with different command sets
    for dev in devices:
        print(f"Trying device: {dev}")
        
        for cmd_idx, cmd_set in enumerate(command_sets):
            try:
                cmd_on = cmd_set['on']
                cmd_off = cmd_set['off']
                
                print(f"  Command set {cmd_idx + 1}: ON={cmd_on.hex()}, OFF={cmd_off.hex()}")
                
                # Try to send ON command
                try:
                    with open(dev, 'wb') as f:
                        f.write(cmd_on)
                        f.flush()
                    print(f"  ✓ USB Relay ON command sent successfully to {dev}")
                except Exception as e:
                    print(f"  ✗ Failed to send ON command to {dev}: {e}")
                    continue
                
                # Wait for the specified duration
                print(f"  Waiting {duration} seconds...")
                time.sleep(duration)
                
                # Try to send OFF command
                try:
                    with open(dev, 'wb') as f:
                        f.write(cmd_off)
                        f.flush()
                    print(f"  ✓ USB Relay OFF command sent successfully to {dev}")
                    print(f"🎉 Relay control COMPLETED using {dev} with command set {cmd_idx + 1}")
                    return
                except Exception as e:
                    print(f"  ✗ Failed to send OFF command to {dev}: {e}")
                    # Continue to try next command set instead of giving up completely
                    continue
                    
            except PermissionError:
                print(f"  🔒 Permission denied accessing {dev}. Try running with sudo.")
                break  # Try next device
            except Exception as e:
                print(f"  💥 Unexpected error with command set {cmd_idx + 1}: {e}")
                continue  # Try next command set

    print(f"❌ All candidate devices and command sets tried and failed for: {hidraw_path}")
    print("💡 Try running with sudo, or check if relay is properly connected")
    print("💡 Available devices:", glob.glob('/dev/hidraw*') + glob.glob('/dev/ttyUSB*'))


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