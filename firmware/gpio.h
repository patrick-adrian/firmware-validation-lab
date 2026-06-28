/*
 * gpio.h - Bit-banged GPIO port modeled after STM32-style registers.
 *
 * The "hardware" is just the register struct, which the caller (or the mock layer)
 * owns. No globals inside the driver -> deterministic, re-entrant, easy to test.
 */
#ifndef GPIO_H
#define GPIO_H

#include <stddef.h>
#include <stdint.h>

#define GPIO_PIN_COUNT 16u   /* MODER uses 2 bits/pin -> 16 pins per 32-bit register */

typedef enum {
    GPIO_OK = 0,
    GPIO_ERR_NULL = -1,
    GPIO_ERR_RANGE = -2,   /* pin index out of range */
} gpio_status_t;

typedef enum {
    GPIO_MODE_INPUT = 0u,
    GPIO_MODE_OUTPUT = 1u,
} gpio_mode_t;

/* STM32-like register bank: MODER (2 bits/pin), ODR (output data), IDR (input data). */
typedef struct {
    uint32_t MODER;   /* mode bits, 2 per pin */
    uint32_t ODR;     /* output data register, 1 bit per pin */
    uint32_t IDR;     /* input data register, 1 bit per pin  */
} gpio_port_t;

int gpio_init(gpio_port_t *port);
int gpio_set_mode(gpio_port_t *port, uint8_t pin, gpio_mode_t mode);
int gpio_set_pin(gpio_port_t *port, uint8_t pin);     /* drive output high */
int gpio_clear_pin(gpio_port_t *port, uint8_t pin);   /* drive output low  */
int gpio_toggle_pin(gpio_port_t *port, uint8_t pin);
int gpio_read_pin(const gpio_port_t *port, uint8_t pin); /* returns 0/1 or negative error */

#endif /* GPIO_H */
