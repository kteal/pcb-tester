#! /usr/bin/env python3

"""Demonstrate the use of a device parameter to control the Digital Discovery LED brightness.

The Digital Discovery has a multicolor LED that is emitting blue light when nobody is connected to it,
and green light if a connection is active.

By setting the 'LedBrightness' device parameter we can change its brightness from 0 to 100%.
"""

import time
import math
import argparse

from pydwf import DwfLibrary, DwfDeviceParameter, PyDwfError
from pydwf.utilities import openDwfDevice


def demo_led_brightness_device_parameter(device, modulation_frequency):
    """Demonstrate usage of a device parameter to control the LED of a Digilent Discovery."""
    print("Modulating LED frequency at {} Hz. Press CTRL-C to quit.".format(modulation_frequency))
    t0 = time.perf_counter()
    while True:
        t = time.perf_counter() - t0
        brightness = round(50 + 50 * math.sin(t * modulation_frequency * 2.0 * math.pi))
        device.paramSet(DwfDeviceParameter.LedBrightness, brightness)


def main():
    """Parse arguments and start demo."""

    parser = argparse.ArgumentParser(description="Demonstrate LED control for the Digital Discovery.")

    DEFAULT_MODULATION_FREQUENCY = 1.0

    parser.add_argument(
            "-sn", "--serial-number-filter",
            type=str,
            nargs='?',
            dest="serial_number_filter",
            help="serial number filter to select a specific Digilent Waveforms device"
        )

    parser.add_argument(
            "-f", "--modulation-frequency",
            type=float,
            default=DEFAULT_MODULATION_FREQUENCY,
            dest="modulation_frequency",
            help="LED modulation frequency (default: {} Hz)".format(DEFAULT_MODULATION_FREQUENCY)
        )

    args = parser.parse_args()

    try:
        dwf = DwfLibrary()
        with openDwfDevice(dwf, serial_number_filter=args.serial_number_filter) as device:
            demo_led_brightness_device_parameter(device, args.modulation_frequency)
    except PyDwfError as exception:
        print("PyDwfError:", exception)
    except KeyboardInterrupt:
        print("Keyboard interrupt, ending demo.")


if __name__ == "__main__":
    main()
