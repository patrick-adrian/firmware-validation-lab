/*
 * crc_test.c - Black-box entrypoint for the CRC module.
 *
 * Usage:   crc_test <string>
 * Output:  8-digit lowercase hex CRC-32 of <string>, e.g.
 *              $ crc_test 123456789
 *              cbf43926
 *
 * Special input "CRASH" deliberately dereferences NULL to demonstrate the framework's
 * automatic GDB backtrace capture on SIGSEGV (python -m framework.runner --debug).
 */
#include <stdio.h>
#include <string.h>

#include "../firmware/crc.h"

int main(int argc, char **argv)
{
    if (argc < 2) {
        fprintf(stderr, "usage: %s <string>\n", argv[0]);
        return 2;
    }

    if (strcmp(argv[1], "CRASH") == 0) {
        /* Fault-injection path: NULL deref -> SIGSEGV, caught by framework/gdb.py. */
        volatile uint8_t *p = NULL;
        return (int)*p;
    }

    const char *s = argv[1];
    uint32_t crc = crc32((const uint8_t *)s, strlen(s));
    printf("%08x\n", crc);
    return 0;
}
