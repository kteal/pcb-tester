#! /usr/bin/env python3

"""Demonstrate the simplest way to control the AnalogOut instrument."""

import time
import math
import argparse

from pydwf import DwfLibrary, DwfAnalogOutNode, DwfAnalogOutFunction, DwfAnalogOutIdle, PyDwfError
from pydwf.utilities import openDwfDevice


def demo_simple_analog_out(analogOut):
    """Demonstrate simple analog output control.

    Configure both output channels for square wave output, with 'idle' behavior set to
    drive the initial signal value. But note that we never actually start this waveform generation!

    We just set the signal amplitude in Volt, which changes the output of the idle level of the signal.
    This is the simplest way to directly drive the output of the analog output channels that is also at
    least somewhat performant; setting a single channel's output level in this way takes roughly 0.5 … 1 ms.
    """

    # Reset all channels.
    analogOut.reset(-1)

    CH1 = 0
    CH2 = 1

    for channel_index in (CH1, CH2):

        analogOut.nodeFunctionSet (channel_index, DwfAnalogOutNode.Carrier, DwfAnalogOutFunction.Square)
        analogOut.idleSet         (channel_index, DwfAnalogOutIdle.Initial)
        analogOut.nodeEnableSet   (channel_index, DwfAnalogOutNode.Carrier, True)

    frequency = 1.0  # Hz

    t_stopwatch = 0.0
    counter = 0

    t0 = time.monotonic()

    while True:

        t = time.monotonic() - t0

        vx = 2.5 * math.cos(2 * math.pi * t * frequency)
        vy = 2.5 * math.sin(2 * math.pi * t * frequency)

        # To change the output signal on each of the two channels, we just need to change the channel's
        # amplitude setting.

        analogOut.nodeAmplitudeSet(CH1, DwfAnalogOutNode.Carrier, vx)
        analogOut.nodeAmplitudeSet(CH2, DwfAnalogOutNode.Carrier, vy)

        counter += 1
        if counter == 1000:
            duration = (t - t_stopwatch)  # pylint: disable=superfluous-parens
            print("{:8.3f} loops/sec. Press Control-C to quit.".format(counter / duration))
            counter = 0
            t_stopwatch = t


def main():
    """Parse arguments and start demo."""

    parser = argparse.ArgumentParser(description="Demonstrate simple usage of the AnalogOut functionality.")

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
            demo_simple_analog_out(device.analogOut)
    except PyDwfError as exception:
        print("PyDwfError:", exception)
    except KeyboardInterrupt:
        print("Keyboard interrupt, ending demo.")


if __name__ == "__main__":
    main()
