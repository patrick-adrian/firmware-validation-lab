/*
 * fake_timer.c - Controllable tick source backing timer.c's hw_get_ticks().
 *
 * Tests advance time explicitly, so timer behavior is 100% deterministic and instant.
 */
#include "../firmware/timer.h"
#include "mock_hw.h"

static uint32_t s_ticks;

/* ---- hook consumed by firmware/timer.c ---- */

uint32_t hw_get_ticks(void)
{
    return s_ticks;
}

/* ---- control surface (mock_hw.h) ---- */

void mock_timer_reset(void)
{
    s_ticks = 0;
}

void mock_timer_set_ticks(uint32_t ticks)
{
    s_ticks = ticks;
}

void mock_timer_advance(uint32_t delta)
{
    s_ticks += delta;   /* unsigned wrap is intentional (tests rollover) */
}

uint32_t mock_timer_get_ticks(void)
{
    return s_ticks;
}
