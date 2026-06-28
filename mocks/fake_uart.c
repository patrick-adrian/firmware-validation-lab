/*
 * fake_uart.c - In-memory implementation of the UART hardware hooks.
 *
 * TX: bytes the driver writes are appended to a capture buffer Python can read back.
 * RX: Python pre-loads a feed buffer the driver consumes as if bytes arrived on the wire.
 * tx_ready can be forced low to exercise the driver's back-pressure path deterministically.
 */
#include "../firmware/uart.h"
#include "mock_hw.h"

#include <string.h>

static uint8_t s_tx_capture[MOCK_UART_BUF];
static size_t  s_tx_count;

static uint8_t s_rx_feed[MOCK_UART_BUF];
static size_t  s_rx_len;
static size_t  s_rx_pos;

static int s_tx_ready = 1;

/* ---- hooks consumed by firmware/uart.c ---- */

int hw_uart_tx_ready(void)
{
    return s_tx_ready;
}

void hw_uart_write_byte(uint8_t b)
{
    if (s_tx_count < MOCK_UART_BUF) {
        s_tx_capture[s_tx_count++] = b;
    }
}

int hw_uart_rx_ready(void)
{
    return s_rx_pos < s_rx_len;
}

uint8_t hw_uart_read_byte(void)
{
    if (s_rx_pos < s_rx_len) {
        return s_rx_feed[s_rx_pos++];
    }
    return 0u;
}

/* ---- control surface (mock_hw.h) ---- */

void mock_uart_reset(void)
{
    s_tx_count = 0;
    s_rx_len = 0;
    s_rx_pos = 0;
    s_tx_ready = 1;
    memset(s_tx_capture, 0, sizeof(s_tx_capture));
    memset(s_rx_feed, 0, sizeof(s_rx_feed));
}

void mock_uart_feed_rx(const uint8_t *data, size_t n)
{
    if (data == NULL) {
        return;
    }
    if (n > MOCK_UART_BUF) {
        n = MOCK_UART_BUF;
    }
    memcpy(s_rx_feed, data, n);
    s_rx_len = n;
    s_rx_pos = 0;
}

size_t mock_uart_tx_count(void)
{
    return s_tx_count;
}

const uint8_t *mock_uart_tx_data(void)
{
    return s_tx_capture;
}

void mock_uart_set_tx_ready(int ready)
{
    s_tx_ready = ready ? 1 : 0;
}
