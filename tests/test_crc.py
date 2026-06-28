"""
test_crc.py - CRC-32 module.

Demonstrates BOTH interaction modes:
  * white-box via ctypes (call crc32() directly, exact vectors)
  * black-box via subprocess (run the crc_test executable, diff stdout)
  * fault injection via the CRASH path (NULL deref -> SIGSEGV, optionally GDB)
"""
import ctypes
import signal

from framework.testkit import load_module, run_c_function, carray, assert_eq, assert_signal


def _crc_lib():
    lib = load_module("crc")
    lib.crc32.restype = ctypes.c_uint32
    lib.crc32.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t]
    return lib


def test_crc_known_vector():
    """The canonical check value: CRC32("123456789") == 0xCBF43926."""
    lib = _crc_lib()
    data = b"123456789"
    buf = carray(data)
    result = lib.crc32(buf, len(data))
    assert_eq(result, 0xCBF43926, "CRC32 check value")


def test_crc_empty_input():
    """CRC of an empty buffer is 0x00000000 (init ^ final xor)."""
    lib = _crc_lib()
    buf = carray(b"")
    assert_eq(lib.crc32(buf, 0), 0x00000000, "empty CRC")


def test_crc_blackbox_matches_library():
    """The black-box executable must agree with the in-process library."""
    lib = _crc_lib()
    data = b"firmware"
    expected = f"{lib.crc32(carray(data), len(data)):08x}"
    proc = run_c_function("crc_test", input="firmware")
    assert_eq(proc.returncode, 0, "crc_test exit code")
    assert_eq(proc.stdout.strip(), expected, "black-box vs library CRC")


def test_crc_corrupted_data_changes_crc():
    """A single corrupted bit must change the CRC (edge case: data corruption)."""
    lib = _crc_lib()
    good = bytearray(b"sensor-reading-42")
    bad = bytearray(good)
    bad[0] ^= 0x01
    c_good = lib.crc32(carray(good), len(good))
    c_bad = lib.crc32(carray(bad), len(bad))
    assert c_good != c_bad, "corruption must alter CRC"


def test_crc_blackbox_crash_is_caught():
    """Fault injection: the CRASH input must terminate via SIGSEGV (signal 11).

    With `--debug`, the runner auto-captures a GDB backtrace for this crash.
    """
    proc = run_c_function("crc_test", input="CRASH")
    assert_signal(proc, signal.SIGSEGV, "CRASH input should segfault")
