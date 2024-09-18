#! /usr/bin/env python3

"""Demonstrate the use of the UART protocol functionality."""

import time
import argparse

from pydwf import DwfLibrary, PyDwfError
from pydwf.utilities import openDwfDevice


def demo_uart_protocol_api(uart):
    """Demonstrate the UART protocol functionality."""

    UART_LOOPBACK_PIN = 0

    uart.reset()

    # Setup UART communication for 115k2 baud, 8N1.
    uart.rateSet(115200.0)
    uart.bitsSet(8)
    uart.paritySet(0)
    uart.stopSet(1)

    # Setup loopback from TX to RX, both on the same digital I/O pin; no need to connect a physical wire.
    uart.txSet(UART_LOOPBACK_PIN)
    uart.rxSet(UART_LOOPBACK_PIN)

    # Before starting to receive, we must initialize reception by calling the rx() method with size 0.
    uart.rx(0)

    # Loop until interrupted: repeatedly send and receive messages.
    i = 0
    while True:
        message = "UART message #{}".format(i).encode()
        uart.tx(message)
        (rx_buffer, parity_status) = uart.rx(100)
        print("Received message {} with parity status {}".format(rx_buffer, parity_status))
        time.sleep(0.100)
        i += 1


def main():
    """Parse arguments and start demo."""

    parser = argparse.ArgumentParser(description="Demonstrate usage of the UART protocol API.")

    parser.add_argument(
            "-sn", "--serial-number-filter",
            type=str,
            nargs='?',
            dest="serial_number_filter",
            help="serial number filter to select a specific Digilent Waveforms device"
        )

    args = parser.parse_args()

    try:
        dwf = DwfLibrary()
        with openDwfDevice(dwf, serial_number_filter=args.serial_number_filter) as device:
            demo_uart_protocol_api(device.protocol.uart)
    except PyDwfError as exception:
        print("PyDwfError:", exception)
    except KeyboardInterrupt:
        print("Keyboard interrupt, ending demo.")


if __name__ == "__main__":
    main()
