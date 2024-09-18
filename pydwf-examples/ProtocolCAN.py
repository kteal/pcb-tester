#! /usr/bin/env python3

"""Demonstrate the use of the CAN bus protocol functionality."""

import time
import argparse

from pydwf import DwfLibrary, PyDwfError
from pydwf.utilities import openDwfDevice


def demo_can_protocol_api(can) -> None:
    """Demonstrate the CAN bus protocol functionality."""

    CAN_LOOPBACK_PIN = 0

    can.reset()

    # Setup CAN communication for 125 kilobits/sec.
    can.rateSet(125000.0)
    can.polaritySet(0)

    # Loopback TX to RX, both on the same digital I/O pin; no need to connect a physical loopback wire.
    can.txSet(CAN_LOOPBACK_PIN)
    can.rxSet(CAN_LOOPBACK_PIN)

    # Before starting to transmit, we must initialize transmission by calling the tx() method with vID equal to -1.
    can.tx(-1, 0, 0, b"")

    # Before starting to receive, we must initialize reception by calling the rx() method with size 0.
    (v_id, extended, remote, data, status) = can.rx(0)

    # Loop until interrupted: repeatedly send and receive messages.
    i = 0
    while True:
        message = "CAN_{:04x}".format(i).encode()
        can.tx(17, 0, 0, message)
        (v_id, extended, remote, data, status) = can.rx(8)
        print("Received message {} ; vID = {}, extended = {}, remote = {}, status = {}".format(
            data, v_id, extended, remote, status))
        time.sleep(0.100)
        i = (i + 1) % 0x10000


def main():
    """Parse arguments and start demo."""

    parser = argparse.ArgumentParser(description="Demonstrate usage of the CAN bus protocol API.")

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
            demo_can_protocol_api(device.protocol.can)
    except PyDwfError as exception:
        print("PyDwfError:", exception)
    except KeyboardInterrupt:
        print("Keyboard interrupt, ending demo.")


if __name__ == "__main__":
    main()
