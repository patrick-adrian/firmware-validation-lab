/*
 * uart.h - Buffered UART driver built on two ring buffers (TX + RX).
 *
 * The driver moves bytes between its software FIFOs and the "peripheral" through the
 * hw_uart_* hooks below. The mock layer (mocks/fake_uart.c) implements those hooks with
 * in-memory capture/feed buffers; a real STM32 HAL would implement them against USART
 * registers. The driver source is identical in both cases.
 */
#ifndef UART_H
#define UART_H

#include <stddef.h>
#include <stdint.h>

#include "ring_buffer.h"

typedef enum {
    UART_OK = 0,
    UART_ERR_NULL = -1,
    UART_ERR_TX_FULL = -2,   /* software TX FIFO overflow */
    UART_ERR_RX_EMPTY = -3,  /* no byte available to read  */
} uart_status_t;

typedef struct {
    rb_t tx;   /* outbound software FIFO */
    rb_t rx;   /* inbound software FIFO  */
} uart_t;

/* ---- Hardware abstraction hooks (implemented by mock or real HAL) ---- */
int     hw_uart_tx_ready(void);          /* 1 if the peripheral can accept a byte */
void    hw_uart_write_byte(uint8_t b);   /* push one byte to the peripheral DR    */
int     hw_uart_rx_ready(void);          /* 1 if a byte is waiting in the peripheral */
uint8_t hw_uart_read_byte(void);         /* read one byte from the peripheral DR  */

/* ---- Driver API ---- */
int uart_init(uart_t *u);

/* Queue one byte for transmission. UART_ERR_TX_FULL on software FIFO overflow. */
int uart_send(uart_t *u, uint8_t b);

/* Drain the TX FIFO into the peripheral while it stays ready. Returns bytes written. */
int uart_flush(uart_t *u);

/*
 * Read one byte. First pulls any bytes the peripheral has waiting into the RX FIFO,
 * then pops one. Returns UART_OK and sets *out, or UART_ERR_RX_EMPTY.
 */
int uart_recv(uart_t *u, uint8_t *out);

#endif /* UART_H */
