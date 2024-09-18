#! /usr/bin/env python3

"""This demo shows the effect of the symmetry setting on the different waveforms supported by the AnalogOut instrument.

To run this demo, loop back the CH1 output of the AnalogOut device to the CH1 input of the AnalogIn device.
"""

import argparse

import numpy as np
import matplotlib.pyplot as plt

from analog_output_node_utilities import (get_analog_output_node_settings, set_analog_output_node_settings,
                                          analog_output_signal_simulator)

from pydwf import (DwfLibrary, DwfDevice, DwfEnumConfigInfo, DwfAnalogOutNode, DwfAnalogOutIdle, DwfState,
                   DwfAnalogOutFunction, DwfTriggerSource, DwfAnalogInFilter, DwfAcquisitionMode, PyDwfError)

from pydwf.utilities import openDwfDevice


def analog_output_function_symmetry_demo(device: DwfDevice, num_periods: int) -> None:
    """Demonstrate the effect of different 'symmetry' settings on the analog output functions."""

    # pylint: disable=too-many-locals, too-many-statements, too-many-branches

    analogOut = device.analogOut
    analogIn  = device.analogIn

    if analogOut.count() == 0 or analogIn.channelCount() == 0:
        print("The device has no analog output channels that can be used for this demo.")
        return

    CH1 = 0

    # We don't do Noise, Custom, and Play.
    waveform_functions = [
        DwfAnalogOutFunction.DC,
        DwfAnalogOutFunction.Sine,
        DwfAnalogOutFunction.Square,
        DwfAnalogOutFunction.Triangle,
        DwfAnalogOutFunction.RampUp,
        DwfAnalogOutFunction.RampDown,
        DwfAnalogOutFunction.Pulse,
        DwfAnalogOutFunction.Trapezium,
        DwfAnalogOutFunction.SinePower
    ]

    input_frequency_setpoint = 1e6 # 1 MHz

    symmetry_setpoint = 0
    stepsize = 5

    while True:

        plt.clf()

        plt.gcf().set_size_inches(16, 9)
        plt.subplots_adjust(hspace=0.4)

        plt.suptitle("Effect of the symmetry setting on different wave-shape functions\nsymmetry parameter value = {}".
                     format(symmetry_setpoint))

        for (waveform_index, waveform_func) in enumerate(waveform_functions, 1):

            # Prepare analog-out device

            analogOut.reset(-1)

            set_analog_output_node_settings(analogOut, CH1, DwfAnalogOutNode.Carrier,
                                            enable    = True,
                                            func      = waveform_func,
                                            frequency = input_frequency_setpoint / 16384 * num_periods,
                                            amplitude = 1.0,
                                            offset    = 0.0,
                                            symmetry  = symmetry_setpoint,
                                            phase     = 0.0)

            carrier_settings = get_analog_output_node_settings(analogOut, CH1, DwfAnalogOutNode.Carrier)

            analogOut.idleSet(CH1, DwfAnalogOutIdle.Initial)

            analogOut.triggerSourceSet(CH1, DwfTriggerSource.PC)

            analogOut.configure(CH1, True)

            # Prepare analog-in device

            analogIn.reset()

            analogIn.frequencySet(input_frequency_setpoint)
            input_frequency = analogIn.frequencyGet()

            input_buffer_size      = analogIn.bufferSizeGet()
            input_capture_duration = input_buffer_size / input_frequency

            analogIn.channelEnableSet(CH1, True)
            analogIn.channelFilterSet(CH1, DwfAnalogInFilter.Average)
            analogIn.channelRangeSet(CH1, 5.0)

            analogIn.acquisitionModeSet(DwfAcquisitionMode.Single)

            analogIn.triggerSourceSet(DwfTriggerSource.PC)

            analogIn.triggerPositionSet(0.5 * input_capture_duration)

            analogIn.configure(False, True)

            # Start both

            while True:
                status = analogIn.status(True)
                if status == DwfState.Armed:
                    break

            device.triggerPC()

            # Monitor analogIn

            while True:
                status = analogIn.status(True)
                if status == DwfState.Done:
                    break

            input_samples = analogIn.statusData(CH1, input_buffer_size)

            t = np.arange(input_buffer_size) / input_frequency
            predicted_samples = analog_output_signal_simulator(carrier_settings, None, None, t)

            # The "x" value goes from 0 to just under num_periods.
            x = np.arange(input_buffer_size) / input_buffer_size * num_periods

            plt.subplot(3, 3, waveform_index)
            plt.title(waveform_func.name)
            plt.xlim(-0.1, num_periods + 0.1)
            plt.ylim(-1.1, 1.1)

            plt.plot(x, predicted_samples, lw=5.0, c='cyan', label="calculated")
            plt.plot(x, input_samples, c='blue', label="measured")
            for period_boundary in range(1, num_periods):
                plt.axvline(period_boundary, c='gray')

            if waveform_index == 1:
                plt.legend(loc="upper left")

            if waveform_index == 8:
                plt.xlabel("period")

            if waveform_index == 4:
                plt.ylabel("signal")

        analogIn.reset()
        analogOut.reset(-1)

        plt.pause(0.200)

        if len(plt.get_fignums()) == 0:
            # User has closed the window, finish.
            break

        # Proceed to next symmetry setting.
        symmetry_setpoint += stepsize
        if abs(symmetry_setpoint) > 100:
            stepsize *= -1
            symmetry_setpoint += 2 * stepsize


def main() -> None:
    """Parse arguments and start demo."""

    parser = argparse.ArgumentParser(
        description="Demonstrate the effect of the AnalogOut instrument's symmetry setting.")

    DEFAULT_NUM_PERIODS = 3

    parser.add_argument(
            "-sn", "--serial-number-filter",
            type=str,
            nargs='?',
            dest="serial_number_filter",
            help="serial number filter to select a specific Digilent Waveforms device"
        )

    parser.add_argument(
            "-np", "--num-periods",
            type=int,
            default=DEFAULT_NUM_PERIODS,
            dest="num_periods",
            help="number of periods of the function (default: {})".format(DEFAULT_NUM_PERIODS)
        )

    args = parser.parse_args()

    def maximize_analog_in_buffer_size(configuration_parameters):
        """Select the configuration with the highest possible analog in buffer size."""
        return configuration_parameters[DwfEnumConfigInfo.AnalogInBufferSize]

    try:
        dwf = DwfLibrary()
        with openDwfDevice(dwf, serial_number_filter=args.serial_number_filter,
                           score_func=maximize_analog_in_buffer_size) as device:
            analog_output_function_symmetry_demo(device, args.num_periods)
    except PyDwfError as exception:
        print("PyDwfError:", exception)
    except KeyboardInterrupt:
        print("Keyboard interrupt, ending demo.")


if __name__ == "__main__":
    main()
