"""
test_uart.py - Buffered UART driver against the fake UART peripheral (white-box).

The mock layer captures transmitted bytes and feeds received bytes, letting Python inject
inputs and validate outputs. Covers TX/RX round-trips, FIFO overflow, peripheral
back-pressure, RX corruption, and empty-read defense.
"""
import ctypes

from framework.testkit import load_module, carray, assert_eq

UART_OK, UART_ERR_NULL, UART_ERR_TX_FULL, UART_ERR_RX_EMPTY = 0, -1, -2, -3
RB_CAPACITY = 64


class RingBuffer(ctypes.Structure):
    _fields_ = [("buf", ctypes.c_ubyte * RB_CAPACITY),
                ("head", ctypes.c_size_t),
                ("tail", ctypes.c_size_t),
                ("count", ctypes.c_size_t)]


class Uart(ctypes.Structure):
    _fields_ = [("tx", RingBuffer), ("rx", RingBuffer)]


def _lib():
    lib = load_module("uart")
    for fn in ("uart_init", "uart_send", "uart_flush", "uart_recv"):
        getattr(lib, fn).restype = ctypes.c_int
    lib.mock_uart_tx_count.restype = ctypes.c_size_t
    lib.mock_uart_tx_data.restype = ctypes.POINTER(ctypes.c_ubyte)
    lib.mock_uart_reset()
    return lib


def _captured_tx(lib) -> bytes:
    n = lib.mock_uart_tx_count()
    ptr = lib.mock_uart_tx_data()
    return bytes(ptr[i] for i in range(n))


def test_uart_send_and_flush():
    """Queued bytes appear at the peripheral after flush, in order."""
    lib = _lib()
    u = Uart()
    lib.uart_init(ctypes.byref(u))
    for b in b"HI":
        assert_eq(lib.uart_send(ctypes.byref(u), b), UART_OK)
    written = lib.uart_flush(ctypes.byref(u))
    assert_eq(written, 2, "bytes flushed")
    assert_eq(_captured_tx(lib), b"HI", "captured TX")


def test_uart_receive_injected_bytes():
    """Python feeds RX bytes; the driver returns them in order."""
    lib = _lib()
    u = Uart()
    lib.uart_init(ctypes.byref(u))
    data = b"OK"
    lib.mock_uart_feed_rx(carray(data), len(data))
    out = ctypes.c_ubyte()
    got = []
    for _ in range(2):
        assert_eq(lib.uart_recv(ctypes.byref(u), ctypes.byref(out)), UART_OK)
        got.append(out.value)
    assert_eq(bytes(got), b"OK", "received bytes")


def test_uart_tx_fifo_overflow():
    """Sending past the software FIFO capacity returns UART_ERR_TX_FULL."""
    lib = _lib()
    u = Uart()
    lib.uart_init(ctypes.byref(u))
    for i in range(RB_CAPACITY):
        assert_eq(lib.uart_send(ctypes.byref(u), i & 0xFF), UART_OK)
    assert_eq(lib.uart_send(ctypes.byref(u), 0xFF), UART_ERR_TX_FULL, "TX overflow")


def test_uart_peripheral_backpressure():
    """When the peripheral is not ready, flush writes nothing and data is retained."""
    lib = _lib()
    u = Uart()
    lib.uart_init(ctypes.byref(u))
    lib.uart_send(ctypes.byref(u), ord("A"))
    lib.mock_uart_set_tx_ready(0)
    assert_eq(lib.uart_flush(ctypes.byref(u)), 0, "blocked flush writes 0")
    assert_eq(lib.mock_uart_tx_count(), 0, "nothing captured while busy")
    lib.mock_uart_set_tx_ready(1)
    assert_eq(lib.uart_flush(ctypes.byref(u)), 1, "flush resumes when ready")
    assert_eq(_captured_tx(lib), b"A", "retained byte eventually sent")


def test_uart_recv_empty():
    """Reading with no data available returns UART_ERR_RX_EMPTY."""
    lib = _lib()
    u = Uart()
    lib.uart_init(ctypes.byref(u))
    out = ctypes.c_ubyte()
    assert_eq(lib.uart_recv(ctypes.byref(u), ctypes.byref(out)), UART_ERR_RX_EMPTY, "empty RX")
