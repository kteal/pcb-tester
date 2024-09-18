#! /usr/bin/env python3

"""
To run this demo program, hook up an ADXL345 to the Analog Discovery as follows:

   Ground <----> Ground
   V+     <----> VCC
   (NC)   ------ CS
   (NC)   ------ INT1
   (NC)   ------ INT2
   (NC)   -----> SDO
   DIO1   -----> SDA
   DIO0  ------> SCL
"""

import time
import argparse

from pydwf import DwfLibrary, PyDwfError
from pydwf.utilities import openDwfDevice


def set_positive_supply_voltage(analogIO, voltage: float):
    """Configure power supply."""
    analogIO.channelNodeSet(0, 0, 1)
    analogIO.channelNodeSet(0, 1, voltage)
    analogIO.enableSet(1)


def demo_i2c_protocol_api(i2c, use_alt_address: bool):
    """Demonstrate the I²C protocol functionality.

    The I²C protocol API has 11 methods.
    """

    ADXL345_DEVICE_ID = 0xe5  # The fixed value in register 0.

    if use_alt_address:
        i2c_address = 0x53
    else:
        i2c_address = 0x1d

    I2C_PIN_SCL = 0  # Digital pin #0
    I2C_PIN_SDA = 1  # Digital pin #1

    I2C_CMD_READ  = (i2c_address << 1) | 0x00
    I2C_CMD_WRITE = (i2c_address << 1) | 0x01

    i2c.reset()

    i2c.stretchSet(1)
    i2c.rateSet(400000.0)  # Max 400 kHz according to the datasheet.
    i2c.readNakSet(1)
    i2c.sclSet(I2C_PIN_SCL)
    i2c.sdaSet(I2C_PIN_SDA)

    time.sleep(0.100)

    # Verify that we're talking to an ADXL345.

    response = i2c.writeRead(I2C_CMD_READ, [0x00], 1)
    device_id = response[1][0]

    if device_id != ADXL345_DEVICE_ID:
        print("No ADXL345 found on I2C address 0x{:02x}!".format(i2c_address))
        print()
        if use_alt_address:
            print("Try running without the --use-alt-address option?")
        else:
            print("Try running with the --use-alt-address option?")

        return

    print("ADXL345 found on I2C address 0x{:02x}; enabling measurements.".format(i2c_address))
    print()

    # Enable measurements (set 'Measure' bit in POWER_CTL register).
    i2c.write(I2C_CMD_WRITE, [0x2d, 0x08])

    # Loop until interrupted.
    while True:

        # Read 6 bytes from ADXL345 register address 0x32 onwards.
        response = i2c.writeRead(I2C_CMD_READ, [0x32], 6)
        axis_data = response[1]

        ax = (axis_data[0] + axis_data[1] * 256 + 32768) % 65536 - 32768
        ay = (axis_data[2] + axis_data[3] * 256 + 32768) % 65536 - 32768
        az = (axis_data[4] + axis_data[5] * 256 + 32768) % 65536 - 32768

        print("\r[I2C] ADXL345: ax {:6} ay {:6} az {:6}".format(ax, ay, az), end="", flush=True)


def main():
    """Parse arguments and start demo."""

    parser = argparse.ArgumentParser(
        description="Demonstrate usage of the I2C protocol API with an ADXL345 accelerometer.")

    parser.add_argument(
            "-sn", "--serial-number-filter",
            type=str,
            nargs='?',
            dest="serial_number_filter",
            help="serial number filter to select a specific Digilent Waveforms device"
        )

    parser.add_argument(
            "--use-alt-address",
            action='store_true',
            dest="use_alt_address",
            help="use alternate I2C address (0x53) instead of default I2C address (0x1d) for the ADXL345."
        )

    args = parser.parse_args()

    try:
        dwf = DwfLibrary()
        with openDwfDevice(dwf, serial_number_filter=args.serial_number_filter) as device:
            set_positive_supply_voltage(device.analogIO, 3.3)
            demo_i2c_protocol_api(device.protocol.i2c, args.use_alt_address)
    except PyDwfError as exception:
        print("PyDwfError:", exception)
    except KeyboardInterrupt:
        print("Keyboard interrupt, ending demo.")


if __name__ == "__main__":
    main()
