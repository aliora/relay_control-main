from models.Rl02_IO import Rl02IO
from models.Rn62_IO import Rn62IO, CH340IO
from models.Jetson_Embed import JetsonEmbed
from models.Raspberry_Embed import RaspberryEmbed
from models.Desktop_Embed import DesktopEmbed


class RelayControl:
    def __init__(self, brand):
        self.brand = brand

        if self.brand == 'rl-02':
            self.relay_instance = Rl02IO()
        elif self.brand == 'rn-62':
            self.relay_instance = Rn62IO()
        elif self.brand == 'ch340':
            self.relay_instance = CH340IO()
        elif self.brand == 'jetson-embed':
            self.relay_instance = JetsonEmbed()
        elif self.brand == 'raspberry-embed':
            self.relay_instance = RaspberryEmbed()
        elif self.brand == 'desktop-embed':
            self.relay_instance = DesktopEmbed()
        else:
            raise ValueError("Unsupported brand for relay control")

    def trigger_relay(self, ip=None, port=None, relay_number=None, duration=100, device_index=None):
        """
        Röle tetikleme metodu
        
        Args:
            ip: IP adresi (CH340 için kullanılmaz)
            port: Port numarası (CH340 için kullanılmaz)
            relay_number: Röle numarası
            duration: Süre (CH340 için kullanılmaz)
            device_index: CH340 için cihaz index'i (birden fazla CH340 varsa)
        """
        if self.brand == 'ch340':
            return self.relay_instance.trigger_relays(ip, port, relay_number, duration, device_index)
        else:
            return self.relay_instance.trigger_relays(ip, port, relay_number, duration)
