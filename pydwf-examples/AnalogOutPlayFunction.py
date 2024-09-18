#! /usr/bin/env python3

"""This demo shows function playback on two analog output channels."""

import argparse

from analog_output_node_utilities import AnalogOutNodeSettings

from pydwf import DwfLibrary, DwfAnalogOutNode, DwfAnalogOutFunction, PyDwfError, DwfDeviceParameter
from pydwf.utilities import openDwfDevice


def demo_analog_output_instrument_api(analogOut, continue_playing: bool,
                                      ch1_settings: AnalogOutNodeSettings, ch2_settings: AnalogOutNodeSettings):
    """Demonstrate the analog output API."""

    channel_count = analogOut.count()

    if channel_count == 0:
        print("The device has no analog output channels that can be used for this demo.")
        return

    analogOut.reset(-1)

    CH1 = 0
    CH2 = 1

    analogOut.nodeEnableSet    (CH1, DwfAnalogOutNode.Carrier, ch1_settings.enable   )
    analogOut.nodeFunctionSet  (CH1, DwfAnalogOutNode.Carrier, ch1_settings.function )
    analogOut.nodeFrequencySet (CH1, DwfAnalogOutNode.Carrier, ch1_settings.frequency)
    analogOut.nodeAmplitudeSet (CH1, DwfAnalogOutNode.Carrier, ch1_settings.amplitude)
    analogOut.nodeOffsetSet    (CH1, DwfAnalogOutNode.Carrier, ch1_settings.offset   )
    analogOut.nodeSymmetrySet  (CH1, DwfAnalogOutNode.Carrier, ch1_settings.symmetry )
    analogOut.nodePhaseSet     (CH1, DwfAnalogOutNode.Carrier, ch1_settings.phase    )

    analogOut.nodeEnableSet    (CH2, DwfAnalogOutNode.Carrier, ch2_settings.enable   )
    analogOut.nodeFunctionSet  (CH2, DwfAnalogOutNode.Carrier, ch2_settings.function )
    analogOut.nodeFrequencySet (CH2, DwfAnalogOutNode.Carrier, ch2_settings.frequency)
    analogOut.nodeAmplitudeSet (CH2, DwfAnalogOutNode.Carrier, ch2_settings.amplitude)
    analogOut.nodeOffsetSet    (CH2, DwfAnalogOutNode.Carrier, ch2_settings.offset   )
    analogOut.nodeSymmetrySet  (CH2, DwfAnalogOutNode.Carrier, ch2_settings.symmetry )
    analogOut.nodePhaseSet     (CH2, DwfAnalogOutNode.Carrier, ch2_settings.phase    )

    nodes = (DwfAnalogOutNode.Carrier, )

    print()
    for node in nodes:
        for channel_index in (CH1, CH2):
            print("=== active settings for channel CH{}, node {!r}:".format(channel_index + 1, node.name))
            print()
            print("    enable ......... : {}"            .format(analogOut.nodeEnableGet   (channel_index, node)))
            print("    function ....... : {}"            .format(analogOut.nodeFunctionGet (channel_index, node).name))
            print("    frequency ...... : {:20.9f} [Hz]" .format(analogOut.nodeFrequencyGet(channel_index, node)))
            print("    amplitude ...... : {:20.9f} [?]"  .format(analogOut.nodeAmplitudeGet(channel_index, node)))
            print("    offset ......... : {:20.9f} [V]"  .format(analogOut.nodeOffsetGet   (channel_index, node)))
            print("    symmetry ....... : {:20.9f} [%]"  .format(analogOut.nodeSymmetryGet (channel_index, node)))
            print("    phase .......... : {:20.9f} [°]"  .format(analogOut.nodePhaseGet    (channel_index, node)))
            print()

    # Configure CH2 to follow CH1.
    analogOut.masterSet(CH2, CH1)

    analogOut.configure(CH1, True)  # Start channels 1 and 2.

    if continue_playing:
        analogOut.device.paramSet(DwfDeviceParameter.OnClose, 0)
    else:
        input("press enter to quit ...")


def main():
    """Parse arguments and start demo."""

    # pylint: disable=too-many-locals

    waveform_map = {
        "dc"        : DwfAnalogOutFunction.DC,
        "sine"      : DwfAnalogOutFunction.Sine,
        "square"    : DwfAnalogOutFunction.Square,
        "triangle"  : DwfAnalogOutFunction.Triangle,
        "ramp-up"   : DwfAnalogOutFunction.RampUp,
        "ramp-down" : DwfAnalogOutFunction.RampDown,
        "noise"     : DwfAnalogOutFunction.Noise,
        "pulse"     : DwfAnalogOutFunction.Pulse,
        "trapezium" : DwfAnalogOutFunction.Trapezium,
        "sinepower" : DwfAnalogOutFunction.SinePower
    }

    parser = argparse.ArgumentParser(description="Demonstrate AnalogOut waveform output.")

    DEFAULT_WAVEFORM  = "sine"
    DEFAULT_FREQUENCY = 1.0e3
    DEFAULT_AMPLITUDE = 5.0
    DEFAULT_OFFSET    = 0.0
    DEFAULT_SYMMETRY  = 50.0
    DEFAULT_PHASE     = 0.0

    parser.add_argument(
            "-sn", "--serial-number-filter",
            type=str,
            nargs='?',
            dest="serial_number_filter",
            help="serial number filter to select a specific Digilent Waveforms device"
        )

    parser.add_argument(
            "-c", "--continue",
            action='store_true',
            dest="continue_playing",
            help="configure instrument to continue playing and quit program immediately"
        )

    parser.add_argument(
            "-w", "--waveform",
            choices=waveform_map,
            default=DEFAULT_WAVEFORM,
            dest="waveform",
            help="waveform be output (default: {})".format(DEFAULT_WAVEFORM)
        )

    parser.add_argument(
            "-f", "--frequency",
            type=float,
            default=DEFAULT_FREQUENCY,
            dest="frequency",
            help="output frequency (default: {} Hz)".format(DEFAULT_FREQUENCY)
        )

    parser.add_argument(
            "-a", "--amplitude",
            type=float,
            default=DEFAULT_AMPLITUDE,
            dest="amplitude",
            help="output amplitude (default: {} V)".format(DEFAULT_AMPLITUDE)
        )

    parser.add_argument(
            "-o", "--offset",
            type=float,
            default=DEFAULT_OFFSET,
            dest="offset",
            help="output offset (default: {} V)".format(DEFAULT_OFFSET)
        )

    parser.add_argument(
            "-s", "--symmetry",
            type=float,
            default=DEFAULT_SYMMETRY,
            dest="symmetry",
            help="output offset (default: {} %%)".format(DEFAULT_SYMMETRY)
        )

    parser.add_argument(
            "-p", "--phase",
            type=float,
            default=DEFAULT_PHASE,
            dest="phase",
            help="output phase (default: {})".format(DEFAULT_PHASE)
        )

    parser.add_argument(
            "-d1", "--default-channel-1",
            action='store_true',
            dest="default_ch1",
            help="ignore command line settings for channel 1, use defaults."
        )
    parser.add_argument(
            "-d2", "--default-channel-2",
            action='store_true',
            dest="default_ch2",
            help="ignore command line settings for channel 2, use defaults."
        )

    args = parser.parse_args()

    arg_settings = AnalogOutNodeSettings(
            True,
            waveform_map[args.waveform],
            args.frequency,
            args.amplitude,
            args.offset,
            args.symmetry,
            args.phase
        )

    default_settings = AnalogOutNodeSettings(
            True,
            waveform_map[DEFAULT_WAVEFORM],
            DEFAULT_FREQUENCY,
            DEFAULT_AMPLITUDE,
            DEFAULT_OFFSET,
            DEFAULT_SYMMETRY,
            DEFAULT_PHASE
        )

    ch1_settings = default_settings if args.default_ch1 else arg_settings
    ch2_settings = default_settings if args.default_ch2 else arg_settings

    try:
        dwf = DwfLibrary()
        with openDwfDevice(dwf, serial_number_filter=args.serial_number_filter) as device:
            demo_analog_output_instrument_api(
                device.analogOut,
                args.continue_playing,
                ch1_settings,
                ch2_settings,
            )
    except PyDwfError as exception:
        print("PyDwfError:", exception)
    except KeyboardInterrupt:
        print("Keyboard interrupt, ending demo.")


if __name__ == "__main__":
    main()
