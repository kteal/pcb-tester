#! /usr/bin/env python3

"""This demo shows analog output of a custom waveform."""

import argparse

import numpy as np

from pydwf import (DwfLibrary, DwfEnumConfigInfo, DwfAnalogOutIdle, DwfTriggerSource, PyDwfError,
                   DwfAnalogOutNode, DwfAnalogOutFunction)
from pydwf.utilities import openDwfDevice


def demo_custom_analog_out_waveform(analogOut, waveform, waveform_duration, wait_duration):
    """Put the given waveform on the first analog output channel."""

    CH1 = 0

    channel = CH1
    node = DwfAnalogOutNode.Carrier

    analogOut.reset(channel)

    # Show the run of the AnalogOut device on trigger pin #0.
    analogOut.device.triggerSet(0, DwfTriggerSource.AnalogOut1)

    analogOut.nodeEnableSet(channel, node, True)
    analogOut.nodeFunctionSet(channel, node, DwfAnalogOutFunction.Custom)

    # Determine offset and amplitude values to use for the requested waveform.

    (amplitude_min, amplitude_max) = analogOut.nodeAmplitudeInfo()  # pylint: disable=unused-variable

    analogOut.nodeAmplitudeSet(channel, node, amplitude_max)
    analogOut.nodeOffsetSet(channel, node, 0.0)

    samples = waveform / amplitude_max
    analogOut.nodeDataSet(channel, node, samples)

    # Wait duration before each waveform emission.
    analogOut.waitSet(channel, wait_duration)

    # The frequency of a custom waveform is (1 / waveform_duration).
    analogOut.nodeFrequencySet(channel, node, 1.0 / waveform_duration)

    # Emit precisely one custom waveform.
    analogOut.runSet(channel, waveform_duration)

    # Keep going indefinitely.
    analogOut.repeatSet(channel, 0)

    analogOut.idleSet(channel, DwfAnalogOutIdle.Initial)

    analogOut.configure(False, True)


def main():
    """Parse arguments and start demo."""

    DEFAULT_WAVEFORM_DURATION = 1e-3
    DEFAULT_WAIT_DURATION  = 0.0

    parser = argparse.ArgumentParser(description="Demonstrate AnalogOut custom waveform playback.")

    parser.add_argument(
            "-sn", "--serial-number-filter",
            type=str,
            nargs='?',
            dest="serial_number_filter",
            help="serial number filter to select a specific Digilent Waveforms device"
        )

    parser.add_argument(
            "-d", "--duration",
            type=float,
            default=DEFAULT_WAVEFORM_DURATION,
            dest="waveform_duration",
            help="output sample frequency, in samples/sec (default: {} s)".format(DEFAULT_WAVEFORM_DURATION)
        )

    parser.add_argument(
            "-w", "--wait",
            type=float,
            default=DEFAULT_WAIT_DURATION,
            dest="wait_duration",
            help="pre-waveform wait (default: {} s)".format(DEFAULT_WAIT_DURATION)
        )

    parser.add_argument(
            "-f", "--filename",
            type=str,
            default=None,
            dest="filename",
            help="file containing the waveform as ASCII floating point numbers (default: none)"
        )

    args = parser.parse_args()

    if args.filename is not None:
        waveform = np.loadtxt(args.filename)
    else:
        # If no filename is given, construct a mildly interesting waveform in the [-2.0 .. 4.0] V range.
        x = np.linspace(-1, 1, 10000)
        w = 0.5 * (1 + np.cos(11 * np.pi*x))
        y = 0.5 * (1 + np.cos(     np.pi*x))
        waveform = -2.0 + w * y * 6.0

    try:
        dwf = DwfLibrary()

        def maximize_analog_out_buffer_size(configuration_parameters):
            """Select the configuration with the highest possible analog out buffer size."""
            return configuration_parameters[DwfEnumConfigInfo.AnalogOutBufferSize]

        with openDwfDevice(dwf, serial_number_filter=args.serial_number_filter,
                           score_func=maximize_analog_out_buffer_size) as device:

            demo_custom_analog_out_waveform(device.analogOut, waveform, args.waveform_duration, args.wait_duration)

            print("Running, press Enter to quit.")
            input()

    except PyDwfError as exception:
        print("PyDwfError:", exception)
    except KeyboardInterrupt:
        print("Keyboard interrupt, ending demo.")


if __name__ == "__main__":
    main()
