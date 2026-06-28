/*
 * mock_hw.h - Control surface for the fake hardware layer.
 *
 * These symbols are exported from the mock .c files and are the knobs Python (via ctypes)
 * uses to inject inputs, force edge cases, and read back captured outputs. Real HAL builds
 * would not include this file at all.
 */
#ifndef MOCK_HW_H
#define MOCK_HW_H

#include <stddef.h>
#include <stdint.h>

/* ---- fake_uart.c ---- */
#define MOCK_UART_BUF 256u

void           mock_uart_reset(void);
/* Queue bytes that the driver will later "receive" from the peripheral. */
void           mock_uart_feed_rx(const uint8_t *data, size_t n);
/* Number of bytes the driver has transmitted (captured TX). */
size_t         mock_uart_tx_count(void);
/* Pointer to the captured TX bytes (valid until next reset/flush). */
const uint8_t *mock_uart_tx_data(void);
/* Force the peripheral busy/ready to test back-pressure (1 = ready, default). */
void           mock_uart_set_tx_ready(int ready);

/* ---- fake_timer.c ---- */
void     mock_timer_reset(void);
void     mock_timer_set_ticks(uint32_t ticks);
void     mock_timer_advance(uint32_t delta);
uint32_t mock_timer_get_ticks(void);

/* ---- fake_gpio.c ---- */
struct gpio_port;                 /* forward decl; real type in firmware/gpio.h */
void              mock_gpio_reset(void);
struct gpio_port *mock_gpio_port(void);   /* shared port instance for black-box harness */
/* Drive the input data register to simulate external pin levels. */
void              mock_gpio_set_idr(uint32_t idr);

#endif /* MOCK_HW_H */
