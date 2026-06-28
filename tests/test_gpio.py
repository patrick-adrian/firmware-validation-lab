"""
test_gpio.py - Bit-banged GPIO registers (white-box via ctypes).

Verifies set/clear/toggle/read bit mechanics, 2-bit mode fields, IDR injection, and
out-of-range pin defense.
"""
import ctypes

from framework.testkit import load_module, assert_eq

GPIO_OK, GPIO_ERR_NULL, GPIO_ERR_RANGE = 0, -1, -2
GPIO_MODE_INPUT, GPIO_MODE_OUTPUT = 0, 1
PIN_COUNT = 16


class GpioPort(ctypes.Structure):
    _fields_ = [("MODER", ctypes.c_uint32),
                ("ODR", ctypes.c_uint32),
                ("IDR", ctypes.c_uint32)]


def _lib():
    lib = load_module("gpio")
    for fn in ("gpio_init", "gpio_set_mode", "gpio_set_pin", "gpio_clear_pin",
               "gpio_toggle_pin", "gpio_read_pin"):
        getattr(lib, fn).restype = ctypes.c_int
    return lib


def test_gpio_set_and_clear():
    lib = _lib()
    p = GpioPort()
    lib.gpio_init(ctypes.byref(p))
    lib.gpio_set_pin(ctypes.byref(p), 3)
    assert_eq(p.ODR, 1 << 3, "set pin 3")
    lib.gpio_clear_pin(ctypes.byref(p), 3)
    assert_eq(p.ODR, 0, "clear pin 3")


def test_gpio_toggle():
    lib = _lib()
    p = GpioPort()
    lib.gpio_init(ctypes.byref(p))
    lib.gpio_toggle_pin(ctypes.byref(p), 7)
    assert_eq(p.ODR, 1 << 7, "toggle on")
    lib.gpio_toggle_pin(ctypes.byref(p), 7)
    assert_eq(p.ODR, 0, "toggle off")


def test_gpio_mode_bits():
    """MODER uses 2 bits per pin; setting pin 5 to OUTPUT sets bits [11:10]."""
    lib = _lib()
    p = GpioPort()
    lib.gpio_init(ctypes.byref(p))
    lib.gpio_set_mode(ctypes.byref(p), 5, GPIO_MODE_OUTPUT)
    assert_eq(p.MODER, GPIO_MODE_OUTPUT << (5 * 2), "mode bits for pin 5")


def test_gpio_read_injected_input():
    """Drive IDR (simulate external pin level) and read it back."""
    lib = _lib()
    p = GpioPort()
    lib.gpio_init(ctypes.byref(p))
    p.IDR = 1 << 9
    assert_eq(lib.gpio_read_pin(ctypes.byref(p), 9), 1, "read high pin")
    assert_eq(lib.gpio_read_pin(ctypes.byref(p), 8), 0, "read low pin")


def test_gpio_out_of_range_pin():
    """Pin index >= 16 must be rejected with GPIO_ERR_RANGE."""
    lib = _lib()
    p = GpioPort()
    lib.gpio_init(ctypes.byref(p))
    assert_eq(lib.gpio_set_pin(ctypes.byref(p), PIN_COUNT), GPIO_ERR_RANGE, "OOB pin")
