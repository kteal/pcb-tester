#! /usr/bin/env python3

"""Demonstrate AnalogIn instrument, ScanScreen and ScanShift acquisition modes."""

import argparse
import time
import matplotlib.pyplot as plt

from pydwf import (DwfLibrary, DwfEnumConfigInfo, DwfAnalogOutNode, DwfAnalogOutFunction, DwfAcquisitionMode,
                   DwfAnalogInFilter, PyDwfError)
from pydwf.utilities import openDwfDevice


def configure_analog_output(analogOut, analog_out_frequency, analog_out_amplitude, analog_out_offset):
    """Configure a cosine signal on channel 1, and a sine signal on channel 2."""

    # pylint: disable = too-many-branches

    CH1 = 0  # This channel will carry a 'cosine' (i.e., precede channel 2 by 90 degrees).
    CH2 = 1  # This channel will carry a 'sine'.

    node = DwfAnalogOutNode.Carrier

    analogOut.reset(-1)  # Reset both channels.

    analogOut.nodeEnableSet   (CH1, node, True)
    analogOut.nodeFunctionSet (CH1, node, DwfAnalogOutFunction.Sine)
    analogOut.nodeFrequencySet(CH1, node, analog_out_frequency)
    analogOut.nodeAmplitudeSet(CH1, node, analog_out_amplitude)
    analogOut.nodeOffsetSet   (CH1, node, analog_out_offset)
    analogOut.nodePhaseSet    (CH1, node, 90.0)

    analogOut.nodeEnableSet   (CH2, node, True)
    analogOut.nodeFunctionSet (CH2, node, DwfAnalogOutFunction.Sine)
    analogOut.nodeFrequencySet(CH2, node, analog_out_frequency)
    analogOut.nodeAmplitudeSet(CH2, node, analog_out_amplitude)
    analogOut.nodeOffsetSet   (CH2, node, analog_out_offset)
    analogOut.nodePhaseSet    (CH2, node, 0.0)

    # Synchronize second channel to first channel. This ensures that they will start simultaneously.
    analogOut.masterSet(CH2, CH1)

    # Start output on first (and second) channel.
    analogOut.configure(CH1, True)


def run_demo(analogIn, scan_mode: str, sample_frequency: float):
    """Configure the analog input, and perform repeated acquisitions and present them graphically."""

    # pylint: disable = too-many-branches

    if scan_mode == 'ScanShift':
        acquisition_mode = DwfAcquisitionMode.ScanShift
    elif scan_mode == 'ScanScreen':
        acquisition_mode = DwfAcquisitionMode.ScanScreen
    else:
        raise ValueError("bad acquisition_mode")

    CH1 = 0
    CH2 = 1

    channels = (CH1, CH2)

    analogIn.reset()

    for channel_index in channels:
        analogIn.channelEnableSet(channel_index, True)
        analogIn.channelFilterSet(channel_index, DwfAnalogInFilter.Decimate)
        analogIn.channelRangeSet (channel_index, 5.0)

    analogIn.acquisitionModeSet(acquisition_mode)
    analogIn.frequencySet(sample_frequency)

    # Calculate number of samples for each acquisition.
    num_samples = analogIn.bufferSizeGet()

    analogIn.configure(False, True)  # Start acquisition sequence.

    p1 = None
    p2 = None
    vline = None

    plt.title("acquisition mode: {}".format(acquisition_mode.name))
    plt.xlabel("samples [-]")
    plt.ylabel("signals [V]")
    plt.ylim(-3, +3)

    while True:

        analogIn.status(True)

        c1 = analogIn.statusData(CH1, num_samples)

        if p1 is None:
            (p1, ) = plt.plot(c1, '.', label="CH1")
        else:
            p1.set_ydata(c1)

        c2 = analogIn.statusData(CH2, num_samples)
        if p2 is None:
            (p2, ) = plt.plot(c2, '.', label="CH2")
            plt.legend(loc="upper left")
        else:
            p2.set_ydata(c2)

        if acquisition_mode == DwfAcquisitionMode.ScanScreen:
            write_index = analogIn.statusIndexWrite()
            if vline is None:
                vline = plt.axvline(write_index, c='red')
            else:
                vline.set_xdata(write_index)

        plt.pause(1e-3)

        if len(plt.get_fignums()) == 0:
            # User has closed the window, finish.
            break


def main():
    """Parse arguments and start demo."""

    parser = argparse.ArgumentParser(description="Demonstrate scan-screen and scan-shift analog input.")

    DEFAULT_SAMPLE_FREQUENCY = 2.0e3
    DEFAULT_ACQUISITION_MODE = "ScanScreen"

    parser.add_argument(
            "-sn", "--serial-number-filter",
            type=str,
            nargs='?',
            dest="serial_number_filter",
            help="serial number filter to select a specific Digilent Waveforms device"
        )

    parser.add_argument(
            "-fs", "--sample-frequency",
            type=float,
            default=DEFAULT_SAMPLE_FREQUENCY,
            dest="sample_frequency",
            help="sample frequency, in samples per second (default: {} Hz)".format(DEFAULT_SAMPLE_FREQUENCY)
        )

    parser.add_argument(
            "-m", "--scan-mode",
            choices=("ScanShift", "ScanScreen"),
            default=DEFAULT_ACQUISITION_MODE,
            dest="scan_mode",
            help="scan mode (default: {})".format(DEFAULT_ACQUISITION_MODE)
        )

    args = parser.parse_args()

    dwf = DwfLibrary()

    def maximize_analog_in_buffer_size(configuration_parameters):
        """Select the configuration with the highest possible analog in buffer size."""
        return configuration_parameters[DwfEnumConfigInfo.AnalogInBufferSize]

    try:
        with openDwfDevice(dwf, serial_number_filter=args.serial_number_filter,
                           score_func=maximize_analog_in_buffer_size) as device:

            analogOut = device.analogOut
            analogIn  = device.analogIn

            # We want to see 2.5 full cycles in the acquisition window.
            analog_out_frequency = 2.5 * args.sample_frequency / analogIn.bufferSizeGet()

            # Signal amplitude in Volt. The AnalogOut instrument can do 5 Vpp, so 2.5 V amplitude is the maximum.
            analog_out_amplitude = 2.5

            # Signal offset in Volt.
            analog_out_offset = 0.0

            print("Configuring analog output signals ({} Hz) ...".format(analog_out_frequency))

            configure_analog_output(analogOut, analog_out_frequency, analog_out_amplitude, analog_out_offset)

            time.sleep(2.0)  # Wait for a bit to ensure the stability of the analog output signals.

            run_demo(analogIn, args.scan_mode, args.sample_frequency)
    except PyDwfError as exception:
        print("PyDwfError:", exception)


if __name__ == "__main__":
    main()
