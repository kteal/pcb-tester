#! /usr/bin/env python3

"""Demonstrate the use of the AnalogIO functionality."""

import time
import argparse

from pydwf import DwfLibrary, PyDwfError
from pydwf.utilities import openDwfDevice


def demo_analog_io_api(analogIO) -> None:
    """Demonstrates the Analog I/O functionality."""

    # pylint: disable=too-many-locals

    analogIO.reset()

    (enableSetSupported, enableStatusSupported) = analogIO.enableInfo()
    enableGet = analogIO.enableGet()
    enableStatus = analogIO.enableStatus()

    print("analogIO.enableSet() supported ......... : {}".format(enableSetSupported))
    print("analogIO.enableStatus() supported ...... : {}".format(enableStatusSupported))
    print("analogIO.enableGet() ................... : {}".format(enableGet))
    print("analogIO.enableStatus() ................ : {}".format(enableStatus))
    print()

    analogIO.status()  # Request status update of all channels.

    channel_count = analogIO.channelCount()
    print("The Analog I/O device has {} channels:".format(channel_count))
    print()

    for channel_index in range(channel_count):
        channel_name = analogIO.channelName(channel_index)
        node_count = analogIO.channelInfo(channel_index)  # Count number of nodes.
        print("Channel #{} ({} of {} channels) named {} has {} nodes:".format(
            channel_index, channel_index + 1, channel_count, channel_name, node_count))
        print()

        for node_index in range(node_count):
            node_name = analogIO.channelNodeName(channel_index, node_index)
            node_info = analogIO.channelNodeInfo(channel_index, node_index)
            node_set_info = analogIO.channelNodeSetInfo(channel_index, node_index)
            node_get = analogIO.channelNodeGet(channel_index, node_index)
            node_status_info = analogIO.channelNodeStatusInfo(channel_index, node_index)
            node_status = analogIO.channelNodeStatus(channel_index, node_index)
            print("    node #{} ({} of {}):".format(node_index, node_index + 1, node_count))
            print("        node_name ............. {}".format(node_name))
            print("        node_info ............. {}".format(node_info))
            print("        node_set_info ......... {}".format(node_set_info))
            print("        node_get .............. {}".format(node_get))
            print("        node_status_info ...... {}".format(node_status_info))
            print("        node_status ........... {}".format(node_status))
            print()


def demo_analog_io_continuous_readout(analogIO, channel_name) -> None:
    """Demonstrate continuous readout of USB monitor using AnalogIO functionality."""

    channel_count = analogIO.channelCount()

    channel_matches = [channel_index for channel_index in range(channel_count)
                       if analogIO.channelName(channel_index)[0] == channel_name]

    if len(channel_matches) != 1:
        raise RuntimeError("Unable to find unique channel {!r}.".format(channel_name))

    channel_index = channel_matches[0]

    node_count = analogIO.channelInfo(channel_index)  # Count number of nodes.

    # Get info on all existing nodes.

    node_info = [analogIO.channelNodeName(channel_index, node_index) for node_index in range(node_count)]

    print("*** Reading {!r} channel nodes, press CTRL-C to stop. ***".format(channel_name))
    print()

    while True:
        analogIO.status()  # Request status update
        node_values = [analogIO.channelNodeStatus(channel_index, node_index) for node_index in range(node_count)]
        print("{}: {}".format(channel_name,
                              " ; ".join("{} = {:.9f} [{}]".format(description.lower(), value, unit)
                                         for ((description, unit), value) in zip(node_info, node_values))))

        # Wait until start of next period.
        time.sleep(-time.time() % 0.500)


def main():
    """Parse arguments and start AnalogIO demo."""

    parser = argparse.ArgumentParser(description="Demonstrate usage of the AnalogIO functionality.")

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
            demo_analog_io_api(device.analogIO)
            demo_analog_io_continuous_readout(device.analogIO, "USB Monitor")
    except PyDwfError as exception:
        print("PyDwfError:", exception)
    except KeyboardInterrupt:
        print("Keyboard interrupt, ending demo.")


if __name__ == "__main__":
    main()
