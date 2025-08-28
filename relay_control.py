from .models.Rl02_IO import Rl02IO
from .models.Rn62_IO import Rn62IO
from .models.Jetson_Embed import JetsonEmbed
from .models.Raspberry_Embed import RaspberryEmbed
from .models.Desktop_Embed import DesktopEmbed


class RelayControl:
    def __init__(self, brand):
        self.brand = brand

        if self.brand == 'rl-02':
            self.relay_instance = Rl02IO()
        elif self.brand == 'rn-62':
            self.relay_instance = Rn62IO()
        elif self.brand == 'jetson-embed':
            self.relay_instance = JetsonEmbed()
        elif self.brand == 'raspberry-embed':
            self.relay_instance = RaspberryEmbed()
        elif self.brand == 'desktop-embed':
            self.relay_instance = DesktopEmbed()
        else:
            raise ValueError("Unsupported brand for relay control")

    def trigger_relay(self, ip, port, relay_number=None, duration=100):
        return self.relay_instance.trigger_relays(ip, port, relay_number, duration)
