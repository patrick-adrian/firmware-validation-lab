/*
 * timer.h - Software timer over a mockable tick source.
 *
 * The driver never reads a real clock directly; it calls hw_get_ticks(), which the
 * mock layer (mocks/fake_timer.c) implements with a controllable counter. That makes
 * every timing test deterministic -- no sleep(), no wall-clock flakiness.
 *
 * Tick arithmetic is done in unsigned 32-bit so counter rollover is handled naturally
 * (elapsed = now - start wraps correctly as long as the interval < 2^32).
 */
#ifndef TIMER_H
#define TIMER_H

#include <stddef.h>
#include <stdint.h>

typedef enum {
    TIMER_OK = 0,
    TIMER_ERR_NULL = -1,
} timer_status_t;

typedef struct {
    uint32_t start;    /* tick at start */
    uint32_t period;   /* timeout in ticks */
    int running;
} timer_t;

/* Hardware abstraction hook: implemented by the mock (or real HAL on STM32). */
uint32_t hw_get_ticks(void);

int timer_start(timer_t *t, uint32_t period_ticks);
int timer_stop(timer_t *t);

/* Ticks elapsed since start (rollover-safe). Returns 0 if t is NULL/stopped. */
uint32_t timer_elapsed(const timer_t *t);

/* 1 if running and elapsed >= period, else 0. Returns 0 if t is NULL. */
int timer_expired(const timer_t *t);

#endif /* TIMER_H */
