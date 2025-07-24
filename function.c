#define _POSIX_C_SOURCE 200809L
#include "function.h"
#include <unistd.h>
#include <stdlib.h>
#include <fcntl.h>

static int str_to_int(const char *s, int len) {
    int val = 0;
    for (int i = 0; i < len; ++i) {
        val = val * 10 + (s[i] - '0');
    }
    return val;
}

void int_to_str(int n, char *buf) {
    char tmp[16];
    int i = 0;
    if (n == 0) {
        buf[0] = '0';
        buf[1] = '\0';
        return;
    }
    while (n > 0 && i < (int)sizeof(tmp)) {
        tmp[i++] = (n % 10) + '0';
        n /= 10;
    }
    int j = 0;
    while (i > 0) {
        buf[j++] = tmp[--i];
    }
    buf[j] = '\0';
}

int read_numbers(const char *filename, int **out_numbers) {
    int fd = open(filename, O_RDONLY);
    if (fd < 0) return -1;

    char ch;
    char buf[32];
    char *buf_ptr = buf;
    int count = -1;
    int capacity = 0;
    int *numbers = NULL;
    int *num_ptr = NULL;
    while (read(fd, &ch, 1) == 1) {
        if (ch == '\n') {
            int len = buf_ptr - buf;
            if (len > 0) {
                int val = str_to_int(buf, len);
                if (count == -1) {
                    count = val;
                    capacity = count;
                    numbers = malloc(sizeof(int) * capacity);
                    if (!numbers) { close(fd); return -1; }
                    num_ptr = numbers;
                } else {
                    *num_ptr++ = val;
                    count--;
                }
                buf_ptr = buf;
            }
        } else {
            *buf_ptr++ = ch;
        }
    }
    int len = buf_ptr - buf;
    if (len > 0) {
        int val = str_to_int(buf, len);
        if (count == -1) {
            count = val;
            capacity = count;
            numbers = malloc(sizeof(int) * capacity);
            if (!numbers) { close(fd); return -1; }
            num_ptr = numbers;
        } else {
            *num_ptr++ = val;
            count--;
        }
    }
    close(fd);
    if (count != 0) { free(numbers); return -1; }

    *out_numbers = numbers;
    return capacity;
}
