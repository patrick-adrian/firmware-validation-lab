/*
 * fake_gpio.c - Shared GPIO port instance for black-box harnesses + IDR injection.
 *
 * GPIO needs no hardware hooks (the register struct IS the hardware), but the mock
 * provides a process-global port so a black-box main() and Python can agree on one
 * bank, plus a helper to drive the input data register (simulate external pin levels).
 */
#include "../firmware/gpio.h"
#include "mock_hw.h"

static gpio_port_t s_port;

void mock_gpio_reset(void)
{
    gpio_init(&s_port);
}

struct gpio_port *mock_gpio_port(void)
{
    return (struct gpio_port *)&s_port;
}

void mock_gpio_set_idr(uint32_t idr)
{
    s_port.IDR = idr;
}
