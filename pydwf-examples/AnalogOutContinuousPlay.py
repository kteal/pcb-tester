#! /usr/bin/env python3

"""This demo shows continuous, synchronized sample playback on two channels."""

import argparse
import numpy as np

from pydwf import DwfLibrary, DwfEnumConfigInfo, DwfAnalogOutNode, DwfAnalogOutFunction, DwfState, PyDwfError
from pydwf.utilities import openDwfDevice


class CircleSampler:
    """This sampler generates XY samples for a circular shape on demand."""

    # pylint: disable=too-few-public-methods

    def __init__(self, channel: str, sample_frequency: float, refresh_frequency: float):
        self.channel = channel
        self.sample_frequency = sample_frequency
        self.refresh_frequency = refresh_frequency
        self.k = 0  # sample index

    def get_samples(self, n: int):
        """Produce samples."""
        t = np.arange(self.k, self.k + n) / self.sample_frequency
        self.k += n

        if self.channel == 'x':
            return np.cos(t * self.refresh_frequency * 2 * np.pi)

        if self.channel == 'y':
            return np.sin(t * self.refresh_frequency * 2 * np.pi)

        raise ValueError()


class RotatingPolygonSampler:
    """This sampler generates XY samples for a polygon shape on demand."""

    # pylint: disable=too-few-public-methods

    def __init__(self, channel: str, sample_frequency: float, refresh_frequency: float,
                 revolutions_per_sec: float, num_points: float, poly_step: int):
        self.channel = channel
        self.sample_frequency = sample_frequency
        self.refresh_frequency = refresh_frequency
        self.revolutions_per_sec = revolutions_per_sec
        self.num_points = num_points
        self.poly_step = poly_step
        self.k = 0  # sample index

    def get_samples(self, n: int):
        """Produce samples."""
        t = np.arange(self.k, self.k + n) / self.sample_frequency
        self.k += n

        tt = t * self.refresh_frequency

        residual = np.mod(tt * self.num_points, 1.0)

        b = np.round(tt * self.num_points - residual)

        h0 = (2.0 * np.pi * self.poly_step / self.num_points) * b
        h1 = (2.0 * np.pi * self.poly_step / self.num_points) * (b + 1)

        x0 = np.cos(h0)
        y0 = np.sin(h0)

        x1 = np.cos(h1)
        y1 = np.sin(h1)

        x = x0 + (x1 - x0) * residual
        y = y0 + (y1 - y0) * residual

        # rotate (x, y) by (revolutions_per_sec * t) revolutions.

        h = 2 * np.pi * self.revolutions_per_sec * t

        if self.channel == 'x':
            return np.cos(h) * x - np.sin(h) * y

        if self.channel == 'y':
            return np.sin(h) * x + np.cos(h) * y

        raise ValueError()


def demo_analog_output_instrument_api(analogOut, shape, sample_frequency,
                                      refresh_frequency, revolutions_per_sec, num_points, poly_step):
    """Demonstrate the analog output API.

    This demo produces a shape on the first two analog output channels that can be viewed
    on an oscilloscope in XY mode.
    """

    # pylint: disable=too-many-locals

    channel_count = analogOut.count()

    if channel_count == 0:
        print("The device has no analog output channels that can be used for this demo.")
        return

    analogOut.reset(-1)

    CH1 = 0
    CH2 = 1

    # The samplers for a given shape return the requested number of samples on demand, for the given channel.
    if shape == 'circle':
        sampler_ch1 = CircleSampler('x', sample_frequency, refresh_frequency)
        sampler_ch2 = CircleSampler('y', sample_frequency, refresh_frequency)
    elif shape == 'poly':
        sampler_ch1 = RotatingPolygonSampler(
            'x', sample_frequency, refresh_frequency, revolutions_per_sec, num_points, poly_step)
        sampler_ch2 = RotatingPolygonSampler(
            'y', sample_frequency, refresh_frequency, revolutions_per_sec, num_points, poly_step)

    analogOut.nodeEnableSet(CH1, DwfAnalogOutNode.Carrier, True)
    analogOut.nodeFunctionSet(CH1, DwfAnalogOutNode.Carrier, DwfAnalogOutFunction.Play)
    analogOut.nodeFrequencySet(CH1, DwfAnalogOutNode.Carrier, sample_frequency)

    analogOut.nodeEnableSet(CH2, DwfAnalogOutNode.Carrier, True)
    analogOut.nodeFunctionSet(CH2, DwfAnalogOutNode.Carrier, DwfAnalogOutFunction.Play)
    analogOut.nodeFrequencySet(CH2, DwfAnalogOutNode.Carrier, sample_frequency)

    # Configure CH2 to follow CH1.
    analogOut.masterSet(CH2, CH1)

    analogOut.configure(CH1, True)  # Start channels 1 and 2.

    while True:

        ch1_status = analogOut.status(CH1)
        ch2_status = analogOut.status(CH2)

        assert (ch1_status == DwfState.Triggered) and (ch2_status == DwfState.Triggered)

        (ch1_data_free, ch1_data_lost, ch1_data_corrupted) = analogOut.nodePlayStatus(CH1, DwfAnalogOutNode.Carrier)
        (ch2_data_free, ch2_data_lost, ch2_data_corrupted) = analogOut.nodePlayStatus(CH2, DwfAnalogOutNode.Carrier)

        if ch1_data_lost != 0 or ch1_data_corrupted != 0 or ch2_data_lost != 0 or ch2_data_corrupted != 0:
            print("ch1 status: {:10} {:10} {:10} ch2 status: {:10} {:10} {:10}".format(
                ch1_data_free, ch1_data_lost, ch1_data_corrupted,
                ch2_data_free, ch2_data_lost, ch2_data_corrupted))

        feed_ch1 = 0
        feed_ch2 = 0

        if ch1_data_free > ch2_data_free:
            if ch1_data_free >= 2048:
                feed_ch1 = ch1_data_free
        else:
            if ch2_data_free >= 2048:
                feed_ch2 = ch2_data_free

        if feed_ch1 > 0:
            print("Transferring {} samples to channel 1.".format(feed_ch1))
            data = sampler_ch1.get_samples(feed_ch1)
            analogOut.nodePlayData(CH1, DwfAnalogOutNode.Carrier, data)

        if feed_ch2 > 0:
            print("Transferring {} samples to channel 2.".format(feed_ch2))
            data = sampler_ch2.get_samples(feed_ch2)
            analogOut.nodePlayData(CH2, DwfAnalogOutNode.Carrier, data)


def main():
    """Parse arguments and start demo."""

    parser = argparse.ArgumentParser(description="Demonstrate AnalogOut continuous,"
                                     " synchronous playback of sample data on two channels.")

    DEFAULT_SHAPE = "circle"
    DEFAULT_SAMPLE_FREQUENCY = 48.0e3
    DEFAULT_REFRESH_RATE = 100.0
    DEFAULT_REVOLUTIONS_PER_SECOND = 0.1
    DEFAULT_NUM_POINTS = 5
    DEFAULT_POLY_STEP = 1

    parser.add_argument(
            "-sn", "--serial-number-filter",
            type=str,
            nargs='?',
            dest="serial_number_filter",
            help="serial number filter to select a specific Digilent Waveforms device"
        )

    parser.add_argument(
            "--shape",
            choices=("circle", "poly"),
            default=DEFAULT_SHAPE,
            dest="shape",
            help="shape to be output on CH1:X and CH2:Y (default: {})".format(DEFAULT_SHAPE)
        )

    parser.add_argument(
            "-fs", "--sample-frequency",
            type=float,
            default=DEFAULT_SAMPLE_FREQUENCY,
            dest="sample_frequency",
            help="output sample frequency, in samples/sec (default: {} Hz)".format(DEFAULT_SAMPLE_FREQUENCY)
        )

    parser.add_argument(
            "-fr", "--refresh-frequency",
            type=float,
            default=DEFAULT_REFRESH_RATE,
            dest="refresh_frequency",
            help="number of shape redraws per second (default: {} Hz)".format(DEFAULT_REFRESH_RATE)
        )

    parser.add_argument(
            "-rps", "--revolutions-per-sec",
            type=float,
            default=DEFAULT_REVOLUTIONS_PER_SECOND,
            dest="revolutions_per_sec",
            help="globe revolutions per second (default: {})".format(DEFAULT_REVOLUTIONS_PER_SECOND)
        )

    parser.add_argument(
            "-np", "--num-points",
            type=int,
            default=DEFAULT_NUM_POINTS,
            dest="num_points",
            help="poly mode only: number of poly points (default: {})".format(DEFAULT_NUM_POINTS)
        )

    parser.add_argument(
            "-ps", "--poly-step",
            type=int,
            default=DEFAULT_POLY_STEP,
            dest="poly_step",
            help="poly mode only: steps to the next poly point (default: {})".format(DEFAULT_POLY_STEP)
        )

    args = parser.parse_args()

    try:
        dwf = DwfLibrary()

        def maximize_analog_out_buffer_size(configuration_parameters):
            """Select the configuration with the highest possible analog out buffer size."""
            return configuration_parameters[DwfEnumConfigInfo.AnalogOutBufferSize]

        with openDwfDevice(dwf, serial_number_filter=args.serial_number_filter,
                           score_func=maximize_analog_out_buffer_size) as device:
            demo_analog_output_instrument_api(
                device.analogOut,
                args.shape,
                args.sample_frequency,
                args.refresh_frequency,
                args.revolutions_per_sec,
                args.num_points,
                args.poly_step)
    except PyDwfError as exception:
        print("PyDwfError:", exception)
    except KeyboardInterrupt:
        print("Keyboard interrupt, ending demo.")


if __name__ == "__main__":
    main()
