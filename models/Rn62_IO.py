import socket

try:
    import serial  # type: ignore
    import serial.tools.list_ports  # type: ignore
except ImportError:
    serial = None  # sentinel, pyserial yok
import time


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


# CH340 röle kontrol sınıfı
class CH340IO:
    RELAY_COMMANDS = {
        1: {"on": b'\xA0\x01\x01\xA2', "off": b'\xA0\x01\x00\xA1'}
    }
    RELAY_DELAY = 1

    @staticmethod
    def find_ports():
        if serial is None:
            return []
        ports = serial.tools.list_ports.comports()
        ch340_ports = [port for port in ports if getattr(port, 'vid', None) == 0x1a86 and getattr(port, 'pid', None) == 0x7523]
        ch340_ports.sort(key=lambda p: p.device)
        return ch340_ports

    def trigger_relays(self, ip=None, port=None, relay_number=1, duration=None, device_index=None):
        """
        CH340 USB relay tetikleme metodu
        ip ve port parametreleri diğer röle modellerle uyumluluk için var ama kullanılmaz
        """
        if serial is None:
            print("pyserial modülü yüklü değil. Kurulum: pip install pyserial")
            return False
        
        ports = self.find_ports()
        if not ports:
            print("CH340 cihazı bulunamadı.")
            return False
        
        # Sadece bir cihaz varsa, relay_number ne olursa olsun ilk portu seç
        if device_index is None:
            if len(ports) == 1:
                target_port = ports[0].device
            else:
                print("Birden fazla cihaz var, device_index belirtmelisiniz.")
                return False
        else:
            if device_index >= len(ports):
                print(f"CH340 cihaz index {device_index} bulunamadı.")
                return False
            target_port = ports[device_index].device
        
        print(f"CH340 Converter seçildi: {target_port}")
        
        try:
            with serial.Serial(target_port, baudrate=9600, timeout=1) as ser:
                # Sadece bir röle varsa, relay_number ne olursa olsun 1. röle komutunu kullan
                cmd_on = self.RELAY_COMMANDS.get(relay_number, self.RELAY_COMMANDS[1])["on"]
                cmd_off = self.RELAY_COMMANDS.get(relay_number, self.RELAY_COMMANDS[1])["off"]
                
                ser.write(cmd_on)
                print(f"CH340 röle açıldı: {cmd_on.hex()}")
                time.sleep(self.RELAY_DELAY)
                ser.write(cmd_off)
                print(f"CH340 röle kapatıldı: {cmd_off.hex()}")
            return True
        except Exception as e:
            print(f"CH340 röle kontrolünde hata: {e}")
            return False
