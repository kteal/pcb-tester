#! /usr/bin/env python3

"""This example prints static information about all available analog output channels."""

import argparse

from pydwf import DwfLibrary, PyDwfError, DwfEnumConfigInfo
from pydwf.utilities import openDwfDevice


def enum_values_to_str(values):
    """Summarize a collection of enumeration values as a string."""
    enum_type_name = None
    for value in values:
        if enum_type_name is None:
            enum_type_name = value.__class__.__name__
        elif enum_type_name != value.__class__.__name__:
            raise RuntimeError("Enum values are of different types.")
    return "{}.{{{}}}".format(enum_type_name, "|".join(value.name for value in values))


def show_analog_out_channel_info(analogOut):
    """Print info of all analog output channels and their nodes."""

    channel_count = analogOut.count()

    for channel_index in range(channel_count):

        print("=== AnalogOut channel {} ({} of {}):".format(channel_index, channel_index + 1, channel_count))
        print()
        print("    run ............. : {}".format(analogOut.runInfo(channel_index)))
        print("    wait ............ : {}".format(analogOut.waitInfo(channel_index)))
        print("    repeat .......... : {}".format(analogOut.repeatInfo(channel_index)))
        print("    limitation ...... : {}".format(analogOut.limitationInfo(channel_index)))
        print("    idle ............ : {}".format(enum_values_to_str(analogOut.idleInfo(channel_index))))
        print()

        nodes = analogOut.nodeInfo(channel_index)

        for (node_index, node) in enumerate(nodes, 1):
            print("    === node ........... : {} ({} of {})".format(node, node_index, len(nodes)))
            print()
            print("        function ....... : {}".format(
                enum_values_to_str(analogOut.nodeFunctionInfo(channel_index, node))))
            print("        frequency ...... : {}".format(analogOut.nodeFrequencyInfo(channel_index, node)))
            print("        amplitude ...... : {}".format(analogOut.nodeAmplitudeInfo(channel_index, node)))
            print("        offset ......... : {}".format(analogOut.nodeOffsetInfo(channel_index, node)))
            print("        symmetry ....... : {}".format(analogOut.nodeSymmetryInfo(channel_index, node)))
            print("        phase .......... : {}".format(analogOut.nodePhaseInfo(channel_index, node)))
            print("        data ........... : {}".format(analogOut.nodeDataInfo(channel_index, node)))
            print()


def main():
    """Parse arguments and start demo."""

    parser = argparse.ArgumentParser(description="Show AnalogOut channel information.")

    parser.add_argument(
            "-sn", "--serial-number-filter",
            type=str,
            nargs='?',
            dest="serial_number_filter",
            help="serial number filter to select a specific Digilent Waveforms device"
        )

    args = parser.parse_args()

    def maximize_analog_out_channel_count(configuration_parameters):
        """Select the configuration with the highest possible analog output channel count."""
        return configuration_parameters[DwfEnumConfigInfo.AnalogOutChannelCount]

    try:
        dwf = DwfLibrary()
        with openDwfDevice(dwf, serial_number_filter=args.serial_number_filter,
                           score_func=maximize_analog_out_channel_count) as device:
            show_analog_out_channel_info(device.analogOut)
    except PyDwfError as exception:
        print("PyDwfError:", exception)
    except KeyboardInterrupt:
        print("Keyboard interrupt, ending demo.")


if __name__ == "__main__":
    main()
