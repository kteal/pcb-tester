#! /usr/bin/env python3

"""Spinning Globe example."""

import time
import threading
import queue
import argparse

import numpy as np

from gshhs import ensure_gshhs_zipfile_is_available, read_gshhs_polygons

from pydwf import (DwfLibrary, DwfEnumConfigInfo, DwfAnalogOutNode, DwfAnalogOutFunction,
                   DwfState, DwfTriggerSource, PyDwfError)

from pydwf.utilities import openDwfDevice


def points_to_lines(points):
    """Convert points [p1, p2, p3, ..., pn-1, pn] to lines [p1 p2 p2 p3 p4 ... pn-2 pn-1 pn-1 pn]."""
    return np.hstack((points[:, :1], np.repeat(points[:, 1:-1], 2, axis=1), points[:, -1:]))


def polygon_to_lines_3d(polygon):
    """Convert a single GSHHS polygon to a collection of 3D lines."""
    theta = np.deg2rad(90.0 - polygon.points[:]["latitude" ] / 1e6)
    phi   = np.deg2rad(       polygon.points[:]["longitude"] / 1e6)

    sin_theta = np.sin(theta)

    z = np.cos(phi) * sin_theta  # towards us (out of the screen)
    x = np.sin(phi) * sin_theta  # to the right
    y = np.cos(theta)            # upwards

    points = np.stack((x, y, z))

    return points_to_lines(points)


def polygons_to_lines_3d(polygons):
    """Convert multiple GSHHS polygons to a collection of 3D lines."""
    return np.hstack(tuple(polygon_to_lines_3d(polygon) for polygon in polygons))


def read_gshhs_globe(resolution, polygon_filter_func=None):
    """Read GSHHS vector data and convert it to a collection of 3D lines."""
    assert 1 <= resolution <= 5

    # Select coarse, low, intermediate, high, or full resolution.
    resolution_code = ['c', 'l', 'i', 'h', 'f'][resolution - 1]

    # We read the main dataset and the rivers, this combination gives the nicest pictures.
    gshhs_filenames = [
        "gshhs_{}.b".format(resolution_code),
        "wdb_rivers_{}.b".format(resolution_code)
    ]

    ensure_gshhs_zipfile_is_available()

    polygons = []
    for gshhs_filename in gshhs_filenames:
        print("Reading {!r} ...".format(gshhs_filename))
        polygons.extend(read_gshhs_polygons(gshhs_filename, polygon_filter_func))

    globe = polygons_to_lines_3d(polygons)

    return globe


def make_circle_lines(num_circle_points):
    """This generates line segments of a 2D circle around the origin, as a (2, 2*num_points) array."""

    circle_angles = np.arange(num_circle_points + 1) * (2.0 * np.pi / num_circle_points)

    cx = np.cos(circle_angles)
    cy = np.sin(circle_angles)

    circle_points = np.stack((cx, cy))

    circle_lines = points_to_lines(circle_points)

    return circle_lines


def rotation_matrix(alpha, rx, ry, rz):
    """This generates a 3D rotation matrix, providing clockwise rotation of `alpha` radians
    around the (`rx`, `ry`, `rz`) vector.

    This replicates the standard 3D rotation matrix as used in OpenGL.
    """
    ca = np.cos(alpha)
    sa = np.sin(alpha)

    # Normalize the rotation vector.
    length = np.sqrt(rx*rx + ry*ry + rz*rz)
    nx = rx / length
    ny = ry / length
    nz = rz / length

    m1 = (1 - ca) * np.array([
        [ nx * nx , ny * nx , nz * nx ],
        [ nx * ny , ny * ny , nz * ny ],
        [ nx * nz , ny * nz , nz * nz ]
    ])

    m2 = sa * np.array([
        [  0 , -nz, +ny ],
        [ +nz,   0, -nx ],
        [ -ny, +nx,   0 ]
    ])

    m3 = ca * np.identity(3)

    return m1 + m2 + m3


def frame_producer(globe, circle_lines, samples_per_frame, revolutions_per_frame, event, frame_queue):
    """This function produces frames of XY data for a spinning globe."""

    # pylint: disable=too-many-locals

    frame = 0
    while not event.is_set():

        t1 = time.perf_counter()

        rotation_angle = revolutions_per_frame * frame * 2.0 * np.pi

        m = rotation_matrix(rotation_angle, 0, 1, 0)

        transformed_globe = m.dot(globe)

        # Select only lines with z > 0 (so we don't see the back-side of the globe).
        selection = (transformed_globe[2] >= 0)  # pylint: disable=superfluous-parens
        selection = np.repeat(np.all(selection.reshape(-1, 2), axis=1), 2)
        transformed_globe = transformed_globe[:, selection]

        # Drop the z (depth) component
        projected_globe = transformed_globe[0:2]

        lines_2d = np.hstack((circle_lines, projected_globe))

        lines_2d_lengths = np.linalg.norm(lines_2d[:, 1::2] - lines_2d[:, 0::2], axis=0)

        lines_2d_lengths_cumulative = np.cumsum(lines_2d_lengths)

        total_lines2d_length = lines_2d_lengths_cumulative[-1]

        interp_t = np.hstack((0.0, np.repeat(lines_2d_lengths_cumulative[:-1], 2), total_lines2d_length))

        # We now have a list of 2D lines, with total length 'total_lines2d_length'.
        # Sample this as a path for the scope to follow to obtain all (x, y) samples for a full frame.

        ti = np.linspace(0.0, total_lines2d_length, samples_per_frame)
        xi = np.interp(ti, interp_t, lines_2d[0])
        yi = np.interp(ti, interp_t, lines_2d[1])

        xy = np.stack((xi, yi))  # All samples in this frame.

        t2 = time.perf_counter()

        print("[{}] frame rendered: {} lines (length: {:8.3f}) in {:.6f} ms ({} samples)".format(
            frame, len(lines_2d_lengths), total_lines2d_length, (t2 - t1) * 1000.0, samples_per_frame))

        frame_queue.put(xy)

        frame += 1

    print("End of frame_producer.")


def wait_for_input(event):
    """This function waits for user input (Enter/Return key), then sets the event.

    This function can be run inside a thread to monitor if the user wants to end the execution of a program.
    """
    input()
    event.set()


def spinning_globe_demo(analogOut, resolution, sample_frequency, fps, revolutions_per_sec):
    """This function generates spinning globe data as output on the AnalogOut instrument (CH1=X, CH2=Y)."""

    # pylint: disable=too-many-locals

    channel_count = analogOut.count()

    if channel_count == 0:
        print("The device has no analog output channels that can be used for this demo.")
        return

    # The frame_queue is used to pass frame samples from the frame_producer_thread to this thread.
    frame_queue = queue.Queue(maxsize=5)

    # The event is used to signal the desire to quit the program from the wait_for_input_thread
    # to the frame_producer_thread.
    event = threading.Event()

    # Prepare data for the frame_producer thread.
    samples_per_frame = round(sample_frequency / fps)
    revolutions_per_frame = revolutions_per_sec / fps
    globe = read_gshhs_globe(resolution)
    circle_lines = make_circle_lines(360)

    # Create and start the frame_producer_thread.
    frame_producer_thread = threading.Thread(
        target=frame_producer,
        args=(globe, circle_lines, samples_per_frame, revolutions_per_frame, event, frame_queue))
    frame_producer_thread.start()

    # Create and start the wait_for_input_thread.
    wait_for_input_thread = threading.Thread(target=wait_for_input, args=(event, ))
    wait_for_input_thread.start()

    # Configure the analog output instrument.
    analogOut.reset(-1)

    CH1 = 0
    CH2 = 1

    analogOut.nodeEnableSet(CH1, DwfAnalogOutNode.Carrier, True)
    analogOut.nodeFunctionSet(CH1, DwfAnalogOutNode.Carrier, DwfAnalogOutFunction.Play)
    analogOut.nodeFrequencySet(CH1, DwfAnalogOutNode.Carrier, sample_frequency)
    analogOut.nodeAmplitudeSet(CH1, DwfAnalogOutNode.Carrier, 5.0)

    analogOut.nodeEnableSet(CH2, DwfAnalogOutNode.Carrier, True)
    analogOut.nodeFunctionSet(CH2, DwfAnalogOutNode.Carrier, DwfAnalogOutFunction.Play)
    analogOut.nodeFrequencySet(CH2, DwfAnalogOutNode.Carrier, sample_frequency)
    analogOut.nodeAmplitudeSet(CH2, DwfAnalogOutNode.Carrier, 5.0)

    analogOut.triggerSourceSet(CH1, DwfTriggerSource.PC)

    # Configure CH2 to follow CH1.
    analogOut.masterSet(CH2, CH1)

    analogOut.configure(CH1, True)  # Start channels 1 and 2.

    analogOut.device.triggerPC()

    # Analog-out loop.

    while frame_producer_thread.is_alive() or not frame_queue.empty():

        # Fetch XY data for the next frame.
        xy = frame_queue.get()

        # Push the XY data to the AnalogOut instrument.

        offset = 0
        samples_left = xy.shape[1]

        while samples_left != 0:

            while True:

                ch1_status = analogOut.status(CH1)
                ch2_status = analogOut.status(CH2)

                assert (ch1_status == DwfState.Triggered) and (ch2_status == DwfState.Triggered)

                (ch1_samples_free, UNUSED_ch1_samples_lost, UNUSED_ch1_samples_corrupted) = \
                    analogOut.nodePlayStatus(CH1, DwfAnalogOutNode.Carrier)

                (ch2_samples_free, UNUSED_ch2_samples_lost, UNUSED_ch2_samples_corrupted) = \
                    analogOut.nodePlayStatus(CH2, DwfAnalogOutNode.Carrier)

                transfer_possible = min(ch1_samples_free, ch2_samples_free)

                if transfer_possible >= min(2048, samples_left):
                    break

                # Wait for buffer space to free up in the instrument.
                time.sleep(0.001)

            transfer_samples = min(transfer_possible, samples_left)

            analogOut.nodePlayData(CH1, DwfAnalogOutNode.Carrier, xy[0, offset:offset + transfer_samples])
            analogOut.nodePlayData(CH2, DwfAnalogOutNode.Carrier, xy[1, offset:offset + transfer_samples])

            offset += transfer_samples
            samples_left -= transfer_samples

    # End of analog-out loop; join the threads.

    wait_for_input_thread.join()
    frame_producer_thread.join()


def main():

    """Parse arguments and start Spinning Globe demo."""

    parser = argparse.ArgumentParser(description="Demonstrate AnalogOut continuous,"
                                     " synchronous playback of sample data on two channels.")

    DEFAULT_SAMPLE_FREQUENCY = 600.0e3
    DEFAULT_REFRESH_FREQUENCY = 60.0
    DEFAULT_REVOLUTIONS_PER_SECOND = 0.1
    DEFAULT_GSHHS_RESOLUTION = 2

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
            help="analog output sample frequency (default: {} Hz)".format(DEFAULT_SAMPLE_FREQUENCY)
        )

    parser.add_argument(
            "-fr", "--refresh-frequency",
            type=float,
            default=DEFAULT_REFRESH_FREQUENCY,
            dest="refresh_frequency",
            help="number of shape redraws per second (default: {} Hz)".format(DEFAULT_REFRESH_FREQUENCY)
        )

    parser.add_argument(
            "-rps", "--revolutions-per-sec",
            type=float,
            default=DEFAULT_REVOLUTIONS_PER_SECOND,
            dest="revolutions_per_sec",
            help="globe revolutions per second (default: {})".format(DEFAULT_REVOLUTIONS_PER_SECOND)
        )

    parser.add_argument(
            "-res", "--resolution",
            type=int,
            default=DEFAULT_GSHHS_RESOLUTION,
            dest="resolution",
            help="resolution of GSHHS dataset (1--5, default: {})".format(DEFAULT_GSHHS_RESOLUTION)
        )

    args = parser.parse_args()

    def maximize_analog_out_buffer_size(configuration_parameters):
        """Select the configuration with the highest possible analog out buffer size."""
        return configuration_parameters[DwfEnumConfigInfo.AnalogOutBufferSize]

    try:
        dwf = DwfLibrary()
        with openDwfDevice(dwf, serial_number_filter=args.serial_number_filter,
                           score_func=maximize_analog_out_buffer_size) as device:
            spinning_globe_demo(
                device.analogOut,
                args.resolution,
                args.sample_frequency,
                args.refresh_frequency,
                args.revolutions_per_sec)
    except PyDwfError as exception:
        print("PyDwfError:", exception)
    except KeyboardInterrupt:
        print("Keyboard interrupt, ending demo.")


if __name__ == "__main__":
    main()
