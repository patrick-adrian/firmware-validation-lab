/*
 * gpio.c - Pure bit manipulation over the register struct. No dynamic memory.
 */
#include "gpio.h"

int gpio_init(gpio_port_t *port)
{
    if (port == NULL) {
        return GPIO_ERR_NULL;
    }
    port->MODER = 0u;
    port->ODR = 0u;
    port->IDR = 0u;
    return GPIO_OK;
}

int gpio_set_mode(gpio_port_t *port, uint8_t pin, gpio_mode_t mode)
{
    if (port == NULL) {
        return GPIO_ERR_NULL;
    }
    if (pin >= GPIO_PIN_COUNT) {
        return GPIO_ERR_RANGE;
    }
    uint32_t shift = (uint32_t)pin * 2u;
    port->MODER &= ~(0x3u << shift);
    port->MODER |= ((uint32_t)mode & 0x3u) << shift;
    return GPIO_OK;
}

int gpio_set_pin(gpio_port_t *port, uint8_t pin)
{
    if (port == NULL) {
        return GPIO_ERR_NULL;
    }
    if (pin >= GPIO_PIN_COUNT) {
        return GPIO_ERR_RANGE;
    }
    port->ODR |= (1u << pin);
    return GPIO_OK;
}

int gpio_clear_pin(gpio_port_t *port, uint8_t pin)
{
    if (port == NULL) {
        return GPIO_ERR_NULL;
    }
    if (pin >= GPIO_PIN_COUNT) {
        return GPIO_ERR_RANGE;
    }
    port->ODR &= ~(1u << pin);
    return GPIO_OK;
}

int gpio_toggle_pin(gpio_port_t *port, uint8_t pin)
{
    if (port == NULL) {
        return GPIO_ERR_NULL;
    }
    if (pin >= GPIO_PIN_COUNT) {
        return GPIO_ERR_RANGE;
    }
    port->ODR ^= (1u << pin);
    return GPIO_OK;
}

int gpio_read_pin(const gpio_port_t *port, uint8_t pin)
{
    if (port == NULL) {
        return GPIO_ERR_NULL;
    }
    if (pin >= GPIO_PIN_COUNT) {
        return GPIO_ERR_RANGE;
    }
    return (int)((port->IDR >> pin) & 1u);
}
