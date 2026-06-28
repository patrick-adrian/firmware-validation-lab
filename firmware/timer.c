/*
 * timer.c - Software timer logic. Tick source is injected via hw_get_ticks().
 */
#include "timer.h"

int timer_start(timer_t *t, uint32_t period_ticks)
{
    if (t == NULL) {
        return TIMER_ERR_NULL;
    }
    t->start = hw_get_ticks();
    t->period = period_ticks;
    t->running = 1;
    return TIMER_OK;
}

int timer_stop(timer_t *t)
{
    if (t == NULL) {
        return TIMER_ERR_NULL;
    }
    t->running = 0;
    return TIMER_OK;
}

uint32_t timer_elapsed(const timer_t *t)
{
    if (t == NULL || !t->running) {
        return 0u;
    }
    /* Unsigned subtraction handles 32-bit tick rollover correctly. */
    return hw_get_ticks() - t->start;
}

int timer_expired(const timer_t *t)
{
    if (t == NULL || !t->running) {
        return 0;
    }
    return timer_elapsed(t) >= t->period;
}
