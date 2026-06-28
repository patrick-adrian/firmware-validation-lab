# Firmware Validation Lab - build system.
# Mirrors framework/config.py flags. `make` builds all artifacts into runtime/.
# The Python runner can build on its own (python -m framework.runner); this Makefile
# is the human-facing / CI-facing entrypoint.

CC      ?= gcc
CFLAGS  := -g -O0 -std=c11 -Wall -Wextra -Werror -Ifirmware -Imocks
RUNTIME := runtime

# Optional: `make SANITIZE=1` adds ASan/UBSan.
ifeq ($(SANITIZE),1)
CFLAGS += -fsanitize=address,undefined -fno-omit-frame-pointer
endif

# Shared libraries (ctypes / mock-hardware mode)
LIBS := \
  $(RUNTIME)/libring_buffer.so \
  $(RUNTIME)/libcrc.so \
  $(RUNTIME)/libgpio.so \
  $(RUNTIME)/libtimer.so \
  $(RUNTIME)/libuart.so

# Black-box executables (subprocess / GDB mode)
EXES := $(RUNTIME)/crc_test

.PHONY: all test clean gdb-demo
all: $(LIBS) $(EXES)

$(RUNTIME):
	mkdir -p $(RUNTIME)

# --- shared libraries ---
$(RUNTIME)/libring_buffer.so: firmware/ring_buffer.c | $(RUNTIME)
	$(CC) $(CFLAGS) -fPIC -shared $^ -o $@

$(RUNTIME)/libcrc.so: firmware/crc.c | $(RUNTIME)
	$(CC) $(CFLAGS) -fPIC -shared $^ -o $@

$(RUNTIME)/libgpio.so: firmware/gpio.c mocks/fake_gpio.c | $(RUNTIME)
	$(CC) $(CFLAGS) -fPIC -shared $^ -o $@

$(RUNTIME)/libtimer.so: firmware/timer.c mocks/fake_timer.c | $(RUNTIME)
	$(CC) $(CFLAGS) -fPIC -shared $^ -o $@

$(RUNTIME)/libuart.so: firmware/uart.c firmware/ring_buffer.c mocks/fake_uart.c | $(RUNTIME)
	$(CC) $(CFLAGS) -fPIC -shared $^ -o $@

# --- black-box executables ---
$(RUNTIME)/crc_test: harness/crc_test.c firmware/crc.c | $(RUNTIME)
	$(CC) $(CFLAGS) $^ -o $@

# --- convenience ---
test: all
	python3 -m framework.runner --no-build

gdb-demo: $(RUNTIME)/crc_test
	python3 -m framework.runner --gdb test_crc

clean:
	rm -rf $(RUNTIME)
