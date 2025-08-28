import socket
import os
import glob
import time

try:
    import serial  # type: ignore
    import serial.tools.list_ports  # type: ignore
except ImportError:
    serial = None  # pyserial yok


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


# CH340 röle kontrolü (pyserial yoksa doğrudan /dev üzerinden yazma)
class CH340Relay:
    RELAY_COMMANDS = {
        1: {"on": b'\xA0\x01\x01\xA2', "off": b'\xA0\x01\x00\xA1'}
    }
    RELAY_DELAY = 1

    @staticmethod
    def find_ports():
        # Önce pyserial varsa kullan
        ports = []
        if serial is not None:
            try:
                pts = serial.tools.list_ports.comports()
                for p in pts:
                    ports.append(getattr(p, 'device', str(p)))
            except Exception:
                ports = []

        # Fallback: hidraw veya ttyUSB cihazlarını tara
        if not ports:
            hid = sorted(glob.glob('/dev/hidraw*'))
            tty = sorted(glob.glob('/dev/ttyUSB*'))
            ports = hid + tty

        return ports

    @classmethod
    def trigger(cls, relay_number=1, device_index=None):
        # Eğer pyserial varsa, kullanmayı dener
        ports = cls.find_ports()
        if not ports:
            print("CH340 cihazı bulunamadı.")
            return False

        # Seçilecek port
        if device_index is None:
            if len(ports) == 1:
                target = ports[0]
            else:
                # birden fazla varsa varsayılan ilk
                target = ports[0]
        else:
            if device_index >= len(ports):
                print(f"CH340 cihaz index {device_index} bulunamadı.")
                return False
            target = ports[device_index]

        print(f"CH340 hedef cihaz: {target}")

        cmd_on = cls.RELAY_COMMANDS.get(relay_number, cls.RELAY_COMMANDS[1])["on"]
        cmd_off = cls.RELAY_COMMANDS.get(relay_number, cls.RELAY_COMMANDS[1])["off"]

        # Eğer pyserial mevcut ve hedef bir seri port gibi görünüyorsa pyserial ile dene
        if serial is not None:
            try:
                with serial.Serial(target, baudrate=9600, timeout=1) as ser:
                    ser.write(cmd_on)
                    print(f"CH340 (pyserial) röle açıldı: {cmd_on.hex()}")
                    time.sleep(cls.RELAY_DELAY)
                    ser.write(cmd_off)
                    print(f"CH340 (pyserial) röle kapatıldı: {cmd_off.hex()}")
                return True
            except Exception as e:
                print(f"pyserial ile yazma hatası: {e} — fallback'a geçiliyor")

        # Fallback: doğrudan cihaz dosyasına yaz
        try:
            # open in binary write mode and write raw bytes
            with open(target, 'wb') as f:
                f.write(cmd_on)
                f.flush()
                os.fsync(f.fileno())
            print(f"CH340 (raw) röle açıldı: {cmd_on.hex()}")
            time.sleep(cls.RELAY_DELAY)
            with open(target, 'wb') as f:
                f.write(cmd_off)
                f.flush()
                os.fsync(f.fileno())
            print(f"CH340 (raw) röle kapatıldı: {cmd_off.hex()}")
            return True
        except PermissionError:
            print(f"İzin reddedildi: {target}. sudo ile çalıştırmayı deneyin veya cihaz izinlerini değiştirin.")
            return False
        except Exception as e:
            print(f"CH340 röle kontrolünde hata: {e}")
            return False
