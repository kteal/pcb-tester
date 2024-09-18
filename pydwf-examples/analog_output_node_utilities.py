"""Convenience functions to manipulate AnalogOut instrument nodes, and a (partially complete)
Analog Output signal simulator."""

from typing import Optional, NamedTuple

import numpy as np

from pydwf import DwfAnalogOutFunction, DwfAnalogOutNode


class AnalogOutNodeSettings(NamedTuple):
    """Analog output node settings."""
    enable: bool
    function: DwfAnalogOutFunction
    frequency: float
    amplitude: float
    offset: float
    symmetry: float
    phase: float


def get_analog_output_node_settings(analogOut, channel_index: int, node: DwfAnalogOutNode):
    """Get the settings of an analog output node."""
    return AnalogOutNodeSettings(
            analogOut.nodeEnableGet(channel_index, node),
            analogOut.nodeFunctionGet(channel_index, node),
            analogOut.nodeFrequencyGet(channel_index, node),
            analogOut.nodeAmplitudeGet(channel_index, node),
            analogOut.nodeOffsetGet(channel_index, node),
            analogOut.nodeSymmetryGet(channel_index, node),
            analogOut.nodePhaseGet(channel_index, node)
        )


def set_analog_output_node_settings(analogOut, channel_index: int, node: DwfAnalogOutNode,
                                    enable    : Optional[bool ] = None,
                                    func      : Optional[DwfAnalogOutFunction] = None,
                                    frequency : Optional[float] = None,
                                    amplitude : Optional[float] = None,
                                    offset    : Optional[float] = None,
                                    symmetry  : Optional[float] = None,
                                    phase     : Optional[float] = None):
    """Set the settings of an analog output node."""

    if enable is not None:
        analogOut.nodeEnableSet(channel_index, node, enable)

    if func is not None:
        analogOut.nodeFunctionSet(channel_index, node, func)

    if frequency is not None:
        analogOut.nodeFrequencySet(channel_index, node, frequency)

    if amplitude is not None:
        analogOut.nodeAmplitudeSet(channel_index, node, amplitude)

    if offset is not None:
        analogOut.nodeOffsetSet(channel_index, node, offset)

    if symmetry is not None:
        analogOut.nodeSymmetrySet(channel_index, node, symmetry)

    if phase is not None:
        analogOut.nodePhaseSet(channel_index, node, phase)


def _waveform_triangle(symmetry: float, x):
    x = np.mod(x, 1.0)
    q = np.clip(0.5 * (symmetry / 100.0), 0.000000001, 0.4999999999)
    y = ((2 * q - 1) * (2 * x - 1) + np.abs(q - x) - np.abs(q + x - 1)) / (2 * q * (2 * q - 1))
    return y


def _waveform_square(symmetry: float, x):
    q = np.clip(symmetry / 100.0, 0.0, 1.0)
    if q == 0.0:
        y = np.full_like(x, -1.0)
    else:
        x = np.mod(x, 1.0)
        y = np.sign(q - x)
    return y


def _calculate_signal(settings: AnalogOutNodeSettings, t):

    # pylint: disable=too-many-branches

    x = t * settings.frequency + settings.phase / 360.0

    if settings.function == DwfAnalogOutFunction.DC:

        # All-zero, independent of the symmetry value.
        y = np.zeros_like(x)

    elif settings.function == DwfAnalogOutFunction.Sine:

        # The angle of which the sine is taken varies as a three-part piecewise linear function.
        angle = _waveform_triangle(settings.symmetry, x) * (0.5 * np.pi)

        y = np.sin(angle)

    elif settings.function == DwfAnalogOutFunction.Square:
        # Amplitude in range -1 .. 1
        q = np.clip(settings.symmetry / 100.0, 0.0, 1.0)

        if q == 0.0:
            y = np.full_like(x, -1.0)
        else:
            x = np.mod(x, 1)
            y = np.sign(q - x)

    elif settings.function == DwfAnalogOutFunction.Triangle:

        y = _waveform_triangle(settings.symmetry, x)

    elif settings.function == DwfAnalogOutFunction.RampUp:

        q = np.clip(settings.symmetry / 100.0, 0.0, 1.0)

        if q == 0.0:
            y = np.ones_like(x)
        else:
            x = np.mod(x, 1.0)
            y = (x - np.abs(x - q)) / q

    elif settings.function == DwfAnalogOutFunction.RampDown:

        q = np.clip(settings.symmetry / 100.0, 0.0, 1.0)

        if q == 1.0:
            y = np.ones_like(x)
        else:
            x = np.mod(x, 1.0)
            y = ((x - 1) + np.abs(x - q)) / (q - 1)

    elif settings.function == DwfAnalogOutFunction.Pulse:
        # Amplitude in range 0 .. 1
        y = 0.5 * (1.0 + _waveform_square(settings.symmetry, x))

    elif settings.function == DwfAnalogOutFunction.Trapezium:

        x = np.mod(x, 1.0)

        q = np.clip(0.25 * (settings.symmetry / 100.0), 0.000000001, 0.25)

        y = (-1 + 2*x - np.abs(q - x) + np.abs(q - x + 0.5) + np.abs(q + x - 1.0) - np.abs(q + x - 0.5)) / (2 * q)

    elif settings.function == DwfAnalogOutFunction.SinePower:

        plain_old_sine = np.sin(x * 2 * np.pi)

        # In the SinePower wave function, the 'symmetry' value is abused
        # to indicate and exponent between 1.0 and 0.0.

        exponent_setting = np.clip(settings.symmetry, -99.999999999, 100.000) / 100.0

        if exponent_setting >= 0:
            exponent = (1.0 - exponent_setting)  # pylint: disable=superfluous-parens
        else:
            exponent = 1.0 / (1.0 + exponent_setting)

        y = np.copysign(np.abs(plain_old_sine) ** exponent, plain_old_sine)

    else:
        raise RuntimeError()

    return y


def analog_output_signal_simulator(carrier_settings: AnalogOutNodeSettings,
                                   am_settings: Optional[AnalogOutNodeSettings],
                                   fm_settings: Optional[AnalogOutNodeSettings], t):
    """Predict an AnalogOut waveform based on its parameters."""

    if fm_settings is not None:
        raise RuntimeError("FM modulation not yet supported.")

    if carrier_settings.enable:
        carrier_signal = _calculate_signal(carrier_settings, t)
    else:
        carrier_signal = np.zeros_like(t)

    if am_settings is not None:
        if am_settings.enable:
            am_signal = _calculate_signal(am_settings, t)
            carrier_signal = (100.0 + am_settings.offset + am_settings.amplitude * am_signal) / 100.0 * carrier_signal

    # Note that the carrier offset is always applied, even if the carrier is disabled.
    return carrier_settings.offset + carrier_settings.amplitude * carrier_signal
