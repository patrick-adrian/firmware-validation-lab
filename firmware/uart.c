/*
 * uart.c - Buffered UART driver. Bytes flow: app <-> ring buffers <-> hw_uart_* hooks.
 */
#include "uart.h"

int uart_init(uart_t *u)
{
    if (u == NULL) {
        return UART_ERR_NULL;
    }
    rb_init(&u->tx);
    rb_init(&u->rx);
    return UART_OK;
}

int uart_send(uart_t *u, uint8_t b)
{
    if (u == NULL) {
        return UART_ERR_NULL;
    }
    if (rb_put(&u->tx, b) != RB_OK) {
        return UART_ERR_TX_FULL;
    }
    return UART_OK;
}

int uart_flush(uart_t *u)
{
    if (u == NULL) {
        return UART_ERR_NULL;
    }
    int written = 0;
    uint8_t b;
    while (!rb_is_empty(&u->tx) && hw_uart_tx_ready()) {
        if (rb_get(&u->tx, &b) != RB_OK) {
            break;
        }
        hw_uart_write_byte(b);
        written++;
    }
    return written;
}

int uart_recv(uart_t *u, uint8_t *out)
{
    if (u == NULL || out == NULL) {
        return UART_ERR_NULL;
    }
    /* Pull whatever the peripheral has into the software FIFO first. */
    while (hw_uart_rx_ready() && !rb_is_full(&u->rx)) {
        rb_put(&u->rx, hw_uart_read_byte());
    }
    if (rb_get(&u->rx, out) != RB_OK) {
        return UART_ERR_RX_EMPTY;
    }
    return UART_OK;
}
