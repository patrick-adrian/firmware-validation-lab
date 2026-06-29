/*
 * crc.h - CRC-32 (IEEE 802.3, reflected) over a byte buffer.
 *
 * Parameters: poly=0xEDB88320 (reflected), init=0xFFFFFFFF, final XOR=0xFFFFFFFF.
 * Known vector: crc32("123456789", 9) == 0xCBF43926.
 */
#ifndef CRC_H
#define CRC_H

#include <stddef.h> // for size_t
#include <stdint.h> // for uint32_t

/*
 * Compute CRC-32 over `len` bytes at `data`.
 * If `data` is NULL and `len` is 0, returns the CRC of the empty string (0x00000000).
 * If `data` is NULL and `len` > 0, the result is undefined (intentionally — this is the
 * fault-injection path exercised under GDB).
 */
uint32_t crc32(const uint8_t *data, size_t len);

/* Incremental API for streaming. Seed with crc32_init(), feed, then crc32_final(). */
uint32_t crc32_init(void);
uint32_t crc32_update(uint32_t crc, const uint8_t *data, size_t len);
uint32_t crc32_final(uint32_t crc);

#endif /* CRC_H */
