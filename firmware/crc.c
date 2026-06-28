/*
 * crc.c - Bitwise CRC-32 (IEEE 802.3, reflected). No table, no dynamic memory.
 *
 * Bitwise (vs table-driven) keeps the code tiny and ROM-free, which is the typical
 * tradeoff on a small MCU where flash is scarcer than cycles.
 */
#include "crc.h"

#define CRC32_POLY 0xEDB88320u
#define CRC32_INIT 0xFFFFFFFFu

uint32_t crc32_init(void)
{
    return CRC32_INIT;
}

uint32_t crc32_update(uint32_t crc, const uint8_t *data, size_t len)
{
    for (size_t i = 0; i < len; i++) {
        crc ^= data[i];               /* reflected: xor into low byte */
        for (int bit = 0; bit < 8; bit++) {
            uint32_t mask = (uint32_t)-(int32_t)(crc & 1u);
            crc = (crc >> 1) ^ (CRC32_POLY & mask);
        }
    }
    return crc;
}

uint32_t crc32_final(uint32_t crc)
{
    return crc ^ 0xFFFFFFFFu;
}

uint32_t crc32(const uint8_t *data, size_t len)
{
    uint32_t crc = crc32_update(crc32_init(), data, len);
    return crc32_final(crc);
}
