from relay_control import RelayControl


def main():
    # Rn-62 Example
    relay_control = RelayControl('rn-62')
    relay_control.trigger_relay('10.10.10.180', 9747, relay_number='1')

    # Rl-02 Example
    relay_control.trigger_relay('127.0.0.1', 5050, relay_number=3, duration=100)


if __name__ == "__main__":
    main()
