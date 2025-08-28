#!/usr/bin/env python3
# Küçük test arac31: doğrudan handle_relay fonksiyonunu import edip çağırır
import sys
sys.path.insert(0, '.')
try:
    from servers.raspberry_embed import handle_relay
except Exception as e:
    print('Import hata:', e)
    raise

if __name__ == '__main__':
    import time
    print('Local handle_relay test: tetik 1')
    handle_relay(1)
    time.sleep(1)
    print('Local handle_relay test: tetik 2')
    handle_relay(2)
    print('Bitti')
