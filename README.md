
# Test
Start the test server only when you want to test. No need to remove a server during production
- Run python test_server.py
- Run main.py

# Production

## Trigger a specific relay with relay number
- relay_control = RelayControl('rl-02')
- relay_control.trigger_relay('127.0.0.1', 5050, relay_number=3, duration=100)

## Trigger all relays.
- relay_control = RelayControl('rl-02'')
- relay_control.trigger_relay('127.0.0.1', 5050, duration=100)

## CH340 USB Relay Usage
- ch340_relay = RelayControl('ch340')
- ch340_relay.trigger_relay(relay_number=1)  # IP ve port gerekmez
- ch340_relay.trigger_relay(relay_number=1, device_index=0)  # Birden fazla CH340 varsa

## Supported IO Cards
- Isbitek RL-02
- Runitek RN-62
- CH340 USB Relay Module

## Requirements
- Python native socket library
https://docs.python.org/3/library/socket.html
- pyserial library for CH340 USB relays (pip install pyserial)
