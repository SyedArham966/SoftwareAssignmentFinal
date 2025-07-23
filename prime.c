#define _POSIX_C_SOURCE 200809L
#include "prime.h"
#include <time.h>
#include <unistd.h>

int is_prime(int n) {
    if (n <= 1) return 0;
    if (n <= 3) return 1;
    if (n % 2 == 0) return n == 2;
    struct timespec ts = {0, 1000000};
    for (int i = 3; (long long)i * i <= n; i += 2) {
        if (n % i == 0) return 0;
        nanosleep(&ts, NULL);
    }
    return 1;
}
