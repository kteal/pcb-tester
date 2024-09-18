#! /usr/bin/env python3

"""Demonstrate the use of the DigitalIO functionality."""

import time
import argparse
import random

from pydwf import DwfLibrary, PyDwfError
from pydwf.utilities import openDwfDevice


def demo_digital_io_api(digitalIO) -> None:
    """Demonstrate the Digital I/O functionality."""

    digitalIO.reset()

    print("Pins that support output-enable (i.e., tristate) functionality:")
    print()
    print("  outputEnableInfo (32 bit) ...... : {}0b{:032b}".format(32 * " ", digitalIO.outputEnableInfo()))
    print("  outputEnableInfo (64 bit) ...... : {}0b{:064b}".format( 0 * " ", digitalIO.outputEnableInfo64()))
    print()

    print("Pins for which output-enable is active (i.e. are not tri-stated):")
    print()
    print("  outputEnableGet (32 bit) ....... : {}0b{:032b}".format(32 * " ", digitalIO.outputEnableGet()))
    print("  outputEnableGet (64 bit) ....... : {}0b{:064b}".format( 0 * " ", digitalIO.outputEnableGet64()))
    print()

    print("Pins that are capable of driving output:")
    print()
    print("  outputInfo (32 bit) ............ : {}0b{:032b}".format(32 * " ", digitalIO.outputInfo()))
    print("  outputInfo (64 bit) ............ : {}0b{:064b}".format( 0 * " ", digitalIO.outputInfo64()))
    print()

    print("Pins for which output is set to high:")
    print()
    print("  outputGet (32 bit) ............. : {}0b{:032b}".format(32 * " ", digitalIO.outputGet()))
    print("  outputGet (64 bit) ............. : {}0b{:064b}".format( 0 * " ", digitalIO.outputGet64()))
    print()

    print("Pins that can be used as input:")
    print()
    print("  inputInfo (32 bit) ............. : {}0b{:032b}".format(32 * " ", digitalIO.inputInfo()))
    print("  inputInfo (64 bit) ............. : {}0b{:064b}".format( 0 * " ", digitalIO.inputInfo64()))
    print()

    print("Pin input status:")
    print()
    print("  inputStatus (32 bit) ........... : {}0b{:032b}".format(32 * " ", digitalIO.inputStatus()))
    print("  inputStatus (64 bit) ........... : {}0b{:064b}".format( 0 * " ", digitalIO.inputStatus64()))
    print()

    save_output_bits = digitalIO.outputEnableGet64()
    all_bits = digitalIO.outputInfo64()

    # Enable all outputs
    digitalIO.outputEnableSet64(all_bits)
    try:
        for rep in range(100):  # pylint: disable=unused-variable
            random_bits = random.randrange(0, 2 ** 64) & all_bits
            digitalIO.outputSet64(random_bits)
            print("  outputGet (64 bit) ............. : {}0b{:064b}".format( 0 * " ", digitalIO.outputGet64()))
            print("  inputStatus (64 bit) ........... : {}0b{:064b}".format( 0 * " ", digitalIO.inputStatus64()))
            print()
            time.sleep(0.500)
    finally:
        digitalIO.outputEnableSet64(save_output_bits)


def main():
    """Parse arguments and start demo."""

    parser = argparse.ArgumentParser(description="Demonstrate usage of the DigitalIO functionality.")

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
            demo_digital_io_api(device.digitalIO)
    except PyDwfError as exception:
        print("PyDwfError:", exception)
    except KeyboardInterrupt:
        print("Keyboard interrupt, ending demo.")


if __name__ == "__main__":
    main()
