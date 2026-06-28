"""
test_timer.py - Software timer over a mocked tick source (white-box via ctypes).

Time is advanced explicitly through mock_timer_advance(), so every check is deterministic
and instant -- no sleep(), no flakiness. Also covers 32-bit tick rollover.
"""
import ctypes

from framework.testkit import load_module, assert_eq, assert_true


class Timer(ctypes.Structure):
    _fields_ = [("start", ctypes.c_uint32),
                ("period", ctypes.c_uint32),
                ("running", ctypes.c_int)]


def _lib():
    lib = load_module("timer")
    lib.timer_start.restype = ctypes.c_int
    lib.timer_stop.restype = ctypes.c_int
    lib.timer_elapsed.restype = ctypes.c_uint32
    lib.timer_expired.restype = ctypes.c_int
    lib.mock_timer_get_ticks.restype = ctypes.c_uint32
    lib.mock_timer_reset()
    return lib


def test_timer_not_expired_before_period():
    lib = _lib()
    t = Timer()
    lib.timer_start(ctypes.byref(t), 100)
    lib.mock_timer_advance(50)
    assert_eq(lib.timer_elapsed(ctypes.byref(t)), 50, "elapsed at t+50")
    assert_eq(lib.timer_expired(ctypes.byref(t)), 0, "not expired yet")


def test_timer_expires_at_period():
    lib = _lib()
    t = Timer()
    lib.timer_start(ctypes.byref(t), 100)
    lib.mock_timer_advance(100)
    assert_eq(lib.timer_expired(ctypes.byref(t)), 1, "expired at period")


def test_timer_rollover():
    """Start near UINT32_MAX, advance past the wrap; elapsed math must stay correct."""
    lib = _lib()
    lib.mock_timer_set_ticks(0xFFFFFFF0)  # 16 ticks before wrap
    t = Timer()
    lib.timer_start(ctypes.byref(t), 32)
    lib.mock_timer_advance(48)             # wraps past 0
    assert_eq(lib.timer_elapsed(ctypes.byref(t)), 48, "rollover-safe elapsed")
    assert_true(lib.timer_expired(ctypes.byref(t)) == 1, "expired across rollover")


def test_timer_stopped_reports_zero():
    lib = _lib()
    t = Timer()
    lib.timer_start(ctypes.byref(t), 10)
    lib.timer_stop(ctypes.byref(t))
    lib.mock_timer_advance(100)
    assert_eq(lib.timer_elapsed(ctypes.byref(t)), 0, "stopped timer elapsed")
    assert_eq(lib.timer_expired(ctypes.byref(t)), 0, "stopped timer never expires")
