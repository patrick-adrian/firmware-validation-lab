"""
test_ring_buffer.py - Fixed-capacity ring buffer (white-box via ctypes).

Exercises overflow, underflow, FIFO ordering, wrap-around, and NULL-handle defense.
"""
import ctypes

from framework.testkit import load_module, assert_eq

RB_CAPACITY = 64
RB_OK, RB_ERR_NULL, RB_ERR_FULL, RB_ERR_EMPTY = 0, -1, -2, -3


class RingBuffer(ctypes.Structure):
    _fields_ = [
        ("buf", ctypes.c_ubyte * RB_CAPACITY),
        ("head", ctypes.c_size_t),
        ("tail", ctypes.c_size_t),
        ("count", ctypes.c_size_t),
    ]


def _lib():
    lib = load_module("ring_buffer")
    for fn in ("rb_init", "rb_put", "rb_get", "rb_is_full", "rb_is_empty"):
        getattr(lib, fn).restype = ctypes.c_int
    lib.rb_count.restype = ctypes.c_size_t
    return lib


def test_rb_fifo_order():
    lib = _lib()
    rb = RingBuffer()
    lib.rb_init(ctypes.byref(rb))
    for b in (10, 20, 30):
        assert_eq(lib.rb_put(ctypes.byref(rb), b), RB_OK)
    out = ctypes.c_ubyte()
    got = []
    for _ in range(3):
        lib.rb_get(ctypes.byref(rb), ctypes.byref(out))
        got.append(out.value)
    assert_eq(got, [10, 20, 30], "FIFO ordering")


def test_rb_overflow():
    """put() past capacity returns RB_ERR_FULL and drops nothing already stored."""
    lib = _lib()
    rb = RingBuffer()
    lib.rb_init(ctypes.byref(rb))
    for i in range(RB_CAPACITY):
        assert_eq(lib.rb_put(ctypes.byref(rb), i & 0xFF), RB_OK)
    assert_eq(lib.rb_put(ctypes.byref(rb), 0xAA), RB_ERR_FULL, "overflow")
    assert_eq(lib.rb_is_full(ctypes.byref(rb)), 1)


def test_rb_underflow():
    """get() on empty returns RB_ERR_EMPTY."""
    lib = _lib()
    rb = RingBuffer()
    lib.rb_init(ctypes.byref(rb))
    out = ctypes.c_ubyte()
    assert_eq(lib.rb_get(ctypes.byref(rb), ctypes.byref(out)), RB_ERR_EMPTY, "underflow")


def test_rb_wraparound():
    """Indices must wrap correctly when filled, drained, and refilled."""
    lib = _lib()
    rb = RingBuffer()
    lib.rb_init(ctypes.byref(rb))
    out = ctypes.c_ubyte()
    # Fill, drain half, refill -> forces head/tail past the end of the array.
    for i in range(RB_CAPACITY):
        lib.rb_put(ctypes.byref(rb), i & 0xFF)
    for _ in range(RB_CAPACITY // 2):
        lib.rb_get(ctypes.byref(rb), ctypes.byref(out))
    for i in range(RB_CAPACITY // 2):
        assert_eq(lib.rb_put(ctypes.byref(rb), 100 + i), RB_OK, "refill after wrap")
    assert_eq(lib.rb_count(ctypes.byref(rb)), RB_CAPACITY)


def test_rb_null_handle():
    """NULL handle must be rejected, not dereferenced."""
    lib = _lib()
    assert_eq(lib.rb_put(None, 1), RB_ERR_NULL, "NULL defense")
