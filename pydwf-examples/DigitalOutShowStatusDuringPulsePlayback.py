#! /usr/bin/env python3

"""DigitalOut instrument demo.

Show the behavior of status, run_status, and repeat_status before, during, and after Pulse-mode playback is active.
"""

from typing import Optional, Tuple
import argparse
import time

import numpy as np
import matplotlib.pyplot as plt

from pydwf import (DwfLibrary, DwfEnumConfigInfo, DwfTriggerSource, DwfTriggerSlope, DwfDigitalOutOutput,
                   DwfDigitalOutType, DwfDigitalOutIdle, DwfState, PyDwfError)

from pydwf.utilities import openDwfDevice


def summarize(sequence, separator: str = " followed by ") -> str:
    """Summarize a sequence of values as a string."""
    strings = []

    current = None
    current_count = 0

    for e in sequence:
        if current_count == 0:
            current = e
            current_count = 1
        elif e == current:
            current_count += 1
        else:
            strings.append("{} × {}".format(current_count, current))
            current_count = 1
            current = e

    if current_count != 0:
        strings.append("{} × {}".format(current_count, current))

    return separator.join(strings) if strings else "(none)"


def get_channel_values(digitalOut, func) -> Tuple:
    """Get the result of applying 'func' to all DigitalOut channels."""
    return tuple(func(channel_index) for channel_index in range(digitalOut.count()))


def enum_values_to_str(values):
    """Summarize a collection of enumeration values as a string."""
    enum_type_name = None
    for value in values:
        if enum_type_name is None:
            enum_type_name = value.__class__.__name__
        elif enum_type_name != value.__class__.__name__:
            raise RuntimeError("Enum values are of different types.")
    return "{}.{{{}}}".format(enum_type_name, "|".join(value.name for value in values))


def print_digital_output_info(digitalOut):
    """Print static Info of the DigitalOut instrument.

    Of the 11 queryable "Info" values, 5 are global, and 6 are channel-dependent.
    """

    # pylint: disable=line-too-long, unnecessary-lambda

    channel_count = digitalOut.count()

    print("=== digitalOut global info:")
    print()
    print("    digitalOut.internalClockInfo() ...... : {:10} [Hz]".format(digitalOut.internalClockInfo()))
    print("    digitalOut.triggerSourceInfo() ...... : {}".format(enum_values_to_str(digitalOut.triggerSourceInfo())))
    print("    digitalOut.runInfo() ................ : {} [s]".format(digitalOut.runInfo()))
    print("    digitalOut.waitInfo() ............... : {} [s]".format(digitalOut.waitInfo()))
    print("    digitalOut.repeatInfo() ............. : {} [-]".format(digitalOut.repeatInfo()))
    print()
    print("    NOTE: digitalOut.triggerSourceInfo() is obsolete.")
    print()
    print("=== digitalOut per-channel info --- channel index in range {} .. {} (channel count = {}):".format(0, channel_count - 1, channel_count))
    print()
    print("    digitalOut.outputInfo(idx) .......... : {}".format(summarize(get_channel_values(digitalOut, lambda channel_index: enum_values_to_str(digitalOut.outputInfo(channel_index))))))
    print("    digitalOut.typeInfo(idx) ............ : {}".format(summarize(get_channel_values(digitalOut, lambda channel_index: enum_values_to_str(digitalOut.typeInfo(channel_index))))))
    print("    digitalOut.idleInfo(idx) ............ : {}".format(summarize(get_channel_values(digitalOut, lambda channel_index: enum_values_to_str(digitalOut.idleInfo(channel_index))))))
    print("    digitalOut.dividerInfo(idx) ......... : {}".format(summarize(get_channel_values(digitalOut, lambda channel_index: digitalOut.dividerInfo(channel_index)))))
    print("    digitalOut.counterInfo(idx) ......... : {}".format(summarize(get_channel_values(digitalOut, lambda channel_index: digitalOut.counterInfo(channel_index)))))
    print("    digitalOut.dataInfo(idx) ............ : {}".format(summarize(get_channel_values(digitalOut, lambda channel_index: digitalOut.dataInfo(channel_index)))))
    print()


def print_digital_output_settings(digitalOut):
    """Print regular settings of the DigitalOut instrument.

    Note: a setting is considered "regular" if both a "Set" and "Get" exists for it.

    Of the 14 queryable regular "Get" values, 6 are global, and 8 are channel-dependent.
    """

    # pylint: disable=line-too-long, unnecessary-lambda

    channel_count = digitalOut.count()

    print("=== digitalOut global current settings:")
    print()
    print("    digitalOut.triggerSourceGet() ....... : {}".format(digitalOut.triggerSourceGet()))
    print("    digitalOut.runGet() ................. : {}".format(digitalOut.runGet()))
    print("    digitalOut.waitGet() ................ : {}".format(digitalOut.waitGet()))
    print("    digitalOut.repeatGet() .............. : {}".format(digitalOut.repeatGet()))
    print("    digitalOut.triggerSlopeGet() ........ : {}".format(digitalOut.triggerSlopeGet()))
    print("    digitalOut.repeatTriggerGet() ....... : {}".format(digitalOut.repeatTriggerGet()))
    print()
    print("=== digitalOut per-channel current settings --- channel index in range {} .. {} (channel count = {}):".format(0, channel_count - 1, channel_count))
    print()
    print("    digitalOut.enableGet(idx) ........... : {}".format(summarize(get_channel_values(digitalOut, lambda channel_index: digitalOut.enableGet(channel_index)))))
    print("    digitalOut.outputGet(idx) ........... : {}".format(summarize(get_channel_values(digitalOut, lambda channel_index: digitalOut.outputGet(channel_index)))))
    print("    digitalOut.typeGet(idx) ............. : {}".format(summarize(get_channel_values(digitalOut, lambda channel_index: digitalOut.typeGet(channel_index)))))
    print("    digitalOut.idleGet(idx) ............. : {}".format(summarize(get_channel_values(digitalOut, lambda channel_index: digitalOut.idleGet(channel_index)))))
    print("    digitalOut.dividerInitGet(idx) ...... : {}".format(summarize(get_channel_values(digitalOut, lambda channel_index: digitalOut.dividerInitGet(channel_index)))))
    print("    digitalOut.dividerGet(idx) .......... : {}".format(summarize(get_channel_values(digitalOut, lambda channel_index: digitalOut.dividerGet(channel_index)))))
    print("    digitalOut.counterInitGet(idx) ...... : {}".format(summarize(get_channel_values(digitalOut, lambda channel_index: digitalOut.counterInitGet(channel_index)))))
    print("    digitalOut.counterGet(idx) .......... : {}".format(summarize(get_channel_values(digitalOut, lambda channel_index: digitalOut.counterGet(channel_index)))))
    print()


def change_digital_output_global_settings(
            digitalOut,
            run_duration        : Optional[float],
            wait_duration       : Optional[float],
            repeat_count        : Optional[int],
            repeat_trigger_flag : Optional[bool],
            trigger_source      : Optional[DwfTriggerSource],
            trigger_slope       : Optional[DwfTriggerSlope]
        ):
    """Change global DigitalOut instrument settings, if given."""

    # The DigitalOut device has 14 regular "Set" functions (i.e., Set functions for which there is a Get counterpart).
    # 6 of these are channel independent.

    if trigger_source is not None:
        digitalOut.triggerSourceSet(trigger_source)

    if run_duration is not None:
        digitalOut.runSet(run_duration)

    if wait_duration is not None:
        digitalOut.waitSet(wait_duration)

    if repeat_count is not None:
        digitalOut.repeatSet(repeat_count)

    if trigger_slope is not None:
        digitalOut.triggerSlopeSet(trigger_slope)

    if repeat_trigger_flag is not None:
        digitalOut.repeatTriggerSet(repeat_trigger_flag)


def change_digital_output_channel_settings(
            digitalOut,
            channel_index               : int,
            enable_flag                 : Optional[bool],
            output                      : Optional[DwfDigitalOutOutput],
            type_                       : Optional[DwfDigitalOutType],
            idle_mode                   : Optional[DwfDigitalOutIdle],
            divider_init                : Optional[int],
            divider                     : Optional[int],
            counter_init_high_and_value : Optional[Tuple[bool, int]],
            counter_low_and_high        : Optional[Tuple[int, int]]
        ):
    """Change channel-specific DigitalOut instrument settings, if given."""

    # The DigitalOut device has 14 regular "Set" functions (i.e., Set functions for which there is a Get counterpart).
    # 8 of these are channel independent.

    if enable_flag is not None:
        digitalOut.enableSet(channel_index, enable_flag)

    if output is not None:
        digitalOut.outputSet(channel_index, output)

    if type_ is not None:
        digitalOut.typeSet(channel_index, type_)

    if idle_mode is not None:
        digitalOut.idleSet(channel_index, idle_mode)

    if divider_init is not None:
        digitalOut.dividerInitSet(channel_index, divider_init)

    if divider is not None:
        digitalOut.dividerSet(channel_index, divider)

    if counter_init_high_and_value is not None:
        digitalOut.counterInitSet(channel_index, *counter_init_high_and_value)

    if counter_low_and_high is not None:
        digitalOut.counterSet(channel_index, *counter_low_and_high)


def demo_digital_out_instrument_api(digitalOut):
    """Demonstrate DigitalOut instrument."""

    # pylint: disable = too-many-locals, too-many-statements, too-many-branches

    # - 11 "info" functions;
    # - 14 "get" functions
    # - 14  regular "get" functions (play data functions not included)
    # -  1 "count" function
    # -  8 "other" functions (below).
    #
    # total: 48 functions.

    digitalOut.reset()

    print("===========================================")
    print("===                                     ===")
    print("===  DigitalOut instrument static info  ===")
    print("===                                     ===")
    print("===========================================")
    print()

    print_digital_output_info(digitalOut)

    print("=========================================================")
    print("===                                                   ===")
    print("===  DigitalOut instrument settings just after reset  ===")
    print("===                                                   ===")
    print("=========================================================")
    print()

    print_digital_output_settings(digitalOut)

    change_digital_output_global_settings(
            digitalOut,
            run_duration        = 0.800,
            wait_duration       = 0.200,
            repeat_count        = 4,
            repeat_trigger_flag = False,
            trigger_source      = DwfTriggerSource.PC,
            trigger_slope       = DwfTriggerSlope.Rise
        )

    # Configure channel 0
    change_digital_output_channel_settings(
            digitalOut,
            channel_index               = 0,
            enable_flag                 = True,
            output                      = DwfDigitalOutOutput.PushPull,
            type_                       = DwfDigitalOutType.Pulse,
            idle_mode                   = DwfDigitalOutIdle.Low,
            divider_init                = 0,
            divider                     = 100000,  # counter counts at 1 kHz
            counter_init_high_and_value = (True, 0),
            counter_low_and_high        = (5, 5)
        )

    # Configure channel 1
    change_digital_output_channel_settings(
            digitalOut,
            channel_index               = 1,
            enable_flag                 = True,
            output                      = DwfDigitalOutOutput.PushPull,
            type_                       = DwfDigitalOutType.Pulse,
            idle_mode                   = DwfDigitalOutIdle.Low,
            divider_init                = 10,
            divider                     = 100000,  # counter counts at 1 kHz
            counter_init_high_and_value = (True, 0),
            counter_low_and_high        = (5, 5)
        )

    print("=================================================================")
    print("===                                                           ===")
    print("===  DigitalOut instrument settings just after configuration  ===")
    print("===                                                           ===")
    print("=================================================================")
    print()

    print_digital_output_settings(digitalOut)

    print("========================================")
    print("===                                  ===")
    print("===  DigitalOut instrument starting  ===")
    print("===                                  ===")
    print("========================================")
    print()

    t_slack = 0.500  # slack before trigger and after DwfState.Done
    t_max = 20.0

    trigger_asserted = False
    t_done_seen      = None

    # Start the device.
    digitalOut.configure(True)
    t0 = time.perf_counter()

    status_list = []
    while True:
        # The 'status' call is needed to update the runStatus() and repeatStatus() values.
        status = digitalOut.status()
        t = time.perf_counter() - t0

        if not trigger_asserted:
            if t >= t_slack:
                digitalOut.device.triggerPC()
                trigger_asserted = True
                actual_trigger_time = t

        run_status = digitalOut.runStatus()
        repeat_status = digitalOut.repeatStatus()

        if repeat_status == 65535:
            repeat_status = -1

        repeat_status = round(repeat_status)

        if run_status >= (2**47):
            run_status -= (2**48)

        print("[{:20.9f}] {:20} {:30} {:30}".format(t, status.name, run_status, repeat_status))

        status_list.append((t, status.value, run_status, repeat_status))

        if t_done_seen is None:
            if status == DwfState.Done:
                t_done_seen = t
                t_max = min(t_max, t + t_slack)

        if t > t_max:
            break

        time.sleep(-time.time() % 0.005)

    actual_duration = time.perf_counter() - t0

    expected_duration = (digitalOut.runGet(), digitalOut.waitGet(), digitalOut.repeatGet())

    print()
    print("Sequence done. Total duration: {:.9} [s] (expected: {} [s])".format(actual_duration, expected_duration))

    status_array_dtype = np.dtype([
            ('t', np.float64),
            ('status', np.int32),
            ('run_status', np.float64),
            ('rep_status', np.int32)
        ])

    st = np.array(status_list, dtype=status_array_dtype)

    st["t"] -= actual_trigger_time
    if t_done_seen is not None:
        t_done_seen -= actual_trigger_time

    run_status_valid = (st["run_status"] >= 0)  # pylint: disable=superfluous-parens

    print("Invalid run_status values:", np.unique(st["run_status"][~run_status_valid]))

    st["run_status"][~run_status_valid] = np.nan

    scatter_size = 4.0

    plt.gcf().set_size_inches(16, 9)
    plt.subplots_adjust(hspace=0.4)

    plt.suptitle("DigitalOut status behavior before and during Pulse playback")

    plt.subplot(411)
    plt.grid()
    plt.axvline(0.0, c='red')
    if t_done_seen is not None:
        plt.axvline(t_done_seen, c='red')
    plt.scatter(st["t"], st["status"], s=scatter_size)
    plt.xlim(-t_slack, t_max)
    plt.ylabel("status [DwfState]")

    plt.subplot(412)
    plt.axvline(0.0, c='red')
    if t_done_seen is not None:
        plt.axvline(t_done_seen, c='red')
    plt.scatter(st["t"], run_status_valid, s=scatter_size)
    plt.xlim(-t_slack, t_max)
    plt.ylabel("run_status_valid")

    plt.subplot(413)
    plt.axvline(0.0, c='red')
    if t_done_seen is not None:
        plt.axvline(t_done_seen, c='red')
    plt.scatter(st["t"], st["run_status"] / digitalOut.internalClockInfo(), s=scatter_size)
    plt.xlim(-t_slack, t_max)
    plt.ylabel("run_status [s]")

    plt.subplot(414)
    plt.axvline(0.0, c='red')
    if t_done_seen is not None:
        plt.axvline(t_done_seen, c='red')
    plt.scatter(st["t"], st["rep_status"], s=scatter_size)
    plt.xlim(-t_slack, t_max)
    plt.xlabel("time [s]")
    plt.ylabel("rep_status")

    plt.show()

    # Remaining untested calls:
    #
    # digitalOut.dataSet(channel_index: int, bits: str, tristate: bool=False)
    # digitalOut.playDataSet(rg_bits: int, bits_per_sample: int, count_of_samples: int)
    # digitalOut.playRateSet(rate_hz: float)


def main():
    """Parse arguments and start demo."""

    parser = argparse.ArgumentParser(description="Demonstrate DigitalOut instrument usage.")

    parser.add_argument(
            "-sn", "--serial-number-filter",
            type=str,
            nargs='?',
            dest="serial_number_filter",
            help="serial number filter to select a specific Digilent Waveforms device"
        )

    args = parser.parse_args()

    def maximize_digital_out_buffer_size(configuration_parameters):
        """Select the configuration with the highest possible digital out buffer size."""
        return configuration_parameters[DwfEnumConfigInfo.DigitalOutBufferSize]

    try:
        dwf = DwfLibrary()
        with openDwfDevice(dwf, serial_number_filter=args.serial_number_filter,
                           score_func=maximize_digital_out_buffer_size) as device:
            demo_digital_out_instrument_api(device.digitalOut)
    except PyDwfError as exception:
        print("PyDwfError:", exception)
    except KeyboardInterrupt:
        print("Keyboard interrupt, ending demo.")


if __name__ == "__main__":
    main()
