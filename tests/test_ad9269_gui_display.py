import numpy as np

from daq_pc.ad9269_daq_gui import (
    codes_to_voltage,
    make_dual_envelope,
    select_scope_window,
    voltage_statistics,
)


def test_signed_code_to_module_voltage():
    volts = codes_to_voltage(np.array([-32768, 0, 32767]), 5.0)
    np.testing.assert_allclose(
        volts,
        np.array([-5.0, 0.0, 4.999847412109375]),
        atol=1e-7,
    )


def test_envelope_keeps_peaks_while_smoothing_center_trace():
    a = np.arange(1000, dtype=np.int16)
    b = -a
    a[500] = 30_000
    valid = np.ones(a.size, dtype=np.bool_)

    result = make_dual_envelope(a, b, valid, 100, smooth=True)
    a_min, a_max, a_mean, b_min, b_max, b_mean, bin_valid = result

    assert a_max.max() == 30_000
    assert a_mean.max() < 30_000
    assert b_min.min() == -999
    assert b_max.max() == 0
    assert b_mean.size == 100
    assert bin_valid.all()


def test_scope_window_aligns_rising_crossing_near_twenty_percent():
    rate = 100_000
    samples = 2000
    index = np.arange(samples * 3)
    wave = np.rint(12_000 * np.sin(2.0 * np.pi * 1000 * index / rate)).astype(np.int16)
    valid = np.ones(wave.size, dtype=np.bool_)

    a, b, window_valid, trigger_position, level = select_scope_window(
        wave,
        -wave,
        valid,
        samples,
        trigger_channel=0,
        trigger_mode=0,
        threshold=0,
    )

    assert a.size == samples
    assert b.size == samples
    assert window_valid.all()
    assert 0.19 <= trigger_position <= 0.21
    assert abs(level) < 100
    trigger_index = round(trigger_position * (samples - 1))
    assert a[trigger_index - 1] <= level < a[trigger_index]


def test_voltage_statistics_respect_valid_mask_and_calibration():
    codes = np.array([-32768, -16384, 0, 16384, 32767], dtype=np.int16)
    valid = np.array([False, True, True, True, False])

    result = voltage_statistics(codes, valid, 5.0)

    assert result is not None
    assert result["min_v"] == -2.5
    assert result["max_v"] == 2.5
    assert result["vpp_v"] == 5.0
    assert result["mean_v"] == 0.0
    np.testing.assert_allclose(result["ac_rms_v"], np.sqrt(25.0 / 6.0))
