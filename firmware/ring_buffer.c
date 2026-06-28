/*
 * ring_buffer.c - Fixed-capacity SPSC byte ring buffer (no dynamic memory).
 */
#include "ring_buffer.h"

int rb_init(rb_t *rb)
{
    if (rb == NULL) {
        return RB_ERR_NULL;
    }
    rb->head = 0;
    rb->tail = 0;
    rb->count = 0;
    return RB_OK;
}

int rb_put(rb_t *rb, uint8_t value)
{
    if (rb == NULL) {
        return RB_ERR_NULL;
    }
    if (rb->count >= RB_CAPACITY) {
        return RB_ERR_FULL;
    }
    rb->buf[rb->head] = value;
    rb->head = (rb->head + 1u) % RB_CAPACITY;
    rb->count++;
    return RB_OK;
}

int rb_get(rb_t *rb, uint8_t *out)
{
    if (rb == NULL || out == NULL) {
        return RB_ERR_NULL;
    }
    if (rb->count == 0u) {
        return RB_ERR_EMPTY;
    }
    *out = rb->buf[rb->tail];
    rb->tail = (rb->tail + 1u) % RB_CAPACITY;
    rb->count--;
    return RB_OK;
}

int rb_is_full(const rb_t *rb)
{
    if (rb == NULL) {
        return 1; /* a NULL buffer cannot accept data */
    }
    return rb->count >= RB_CAPACITY;
}

int rb_is_empty(const rb_t *rb)
{
    if (rb == NULL) {
        return 1;
    }
    return rb->count == 0u;
}

size_t rb_count(const rb_t *rb)
{
    if (rb == NULL) {
        return 0u;
    }
    return rb->count;
}
