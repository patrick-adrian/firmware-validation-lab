/*
 * ring_buffer.h - Fixed-capacity single-producer/single-consumer byte ring buffer.
 *
 * Embedded style: no dynamic allocation, all state lives in a caller-owned struct.
 * Used as the backing store for the UART TX/RX queues.
 */
#ifndef RING_BUFFER_H
#define RING_BUFFER_H

#include <stddef.h>
#include <stdint.h>

#define RB_CAPACITY 64u

/* Error codes shared across the firmware modules. */
typedef enum {
    RB_OK = 0,
    RB_ERR_NULL = -1,   /* NULL handle passed in             */
    RB_ERR_FULL = -2,   /* put() on a full buffer (overflow) */
    RB_ERR_EMPTY = -3,  /* get() on an empty buffer          */
} rb_status_t;

typedef struct {
    uint8_t buf[RB_CAPACITY];
    size_t head;   /* write index */
    size_t tail;   /* read index  */
    size_t count;  /* live element count */
} rb_t;

/* Reset a ring buffer to empty. Returns RB_ERR_NULL if rb is NULL. */
int rb_init(rb_t *rb);

/* Push one byte. Returns RB_OK, RB_ERR_FULL, or RB_ERR_NULL. */
int rb_put(rb_t *rb, uint8_t value);

/* Pop one byte into *out. Returns RB_OK, RB_ERR_EMPTY, or RB_ERR_NULL. */
int rb_get(rb_t *rb, uint8_t *out);

/* Introspection helpers (return 0/1; treat NULL as "full/empty" defensively). */
int rb_is_full(const rb_t *rb);
int rb_is_empty(const rb_t *rb);
size_t rb_count(const rb_t *rb);

#endif /* RING_BUFFER_H */
