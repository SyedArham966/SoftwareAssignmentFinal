#define _POSIX_C_SOURCE 200809L
#include "prime.h"
#include "function.h"
#include <unistd.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/wait.h>

int main(int argc, char *argv[]) {
    if (argc != 2) {
        const char msg[] = "Usage: ./prime <file_name>\n";
        write(STDERR_FILENO, msg, sizeof(msg) - 1);
        return 1;
    }

    int *numbers = NULL;
    int num_count = read_numbers(argv[1], &numbers);
    if (num_count <= 0) {
        const char msg[] = "Failed to read numbers\n";
        write(STDERR_FILENO, msg, sizeof(msg) - 1);
        return 1;
    }

    int (*p2c)[2] = malloc(sizeof(int[2]) * num_count);
    int (*c2p)[2] = malloc(sizeof(int[2]) * num_count);
    pid_t *pids = malloc(sizeof(pid_t) * num_count);
    if (!p2c || !c2p || !pids) {
        write(STDERR_FILENO, "Memory alloc error\n", 20);
        free(numbers); free(p2c); free(c2p); free(pids);
        return 1;
    }

    for (int i = 0; i < num_count; ++i) {
        if (pipe(p2c[i]) == -1 || pipe(c2p[i]) == -1) {
            write(STDERR_FILENO, "Pipe error\n", 10);
            free(numbers); free(p2c); free(c2p); free(pids);
            return 1;
        }
    }

    for (int i = 0; i < num_count; ++i) {
        pid_t pid = fork();
        if (pid < 0) {
            write(STDERR_FILENO, "Fork error\n", 11);
            free(numbers); free(p2c); free(c2p); free(pids);
            return 1;
        } else if (pid == 0) {
            for (int j = 0; j < num_count; ++j) {
                if (j != i) {
                    close(p2c[j][0]); close(p2c[j][1]);
                    close(c2p[j][0]); close(c2p[j][1]);
                }
            }
            close(p2c[i][1]);
            close(c2p[i][0]);
            int num;
            if (read(p2c[i][0], &num, sizeof(int)) != sizeof(int)) {
                close(p2c[i][0]);
                close(c2p[i][1]);
                exit(1);
            }
            close(p2c[i][0]);
            int prime = is_prime(num);
            write(c2p[i][1], &prime, sizeof(int));
            close(c2p[i][1]);
            exit(0);
        } else {
            pids[i] = pid;
            close(p2c[i][0]);
            close(c2p[i][1]);
            write(p2c[i][1], &numbers[i], sizeof(int));
            close(p2c[i][1]);
        }
    }

    for (int finished = 0; finished < num_count; ++finished) {
        int status;
        pid_t pid = wait(&status);
        int idx_child = -1;
        for (int i = 0; i < num_count; ++i) {
            if (pids[i] == pid) { idx_child = i; break; }
        }
        if (idx_child >= 0) {
            int res = 0;
            if (read(c2p[idx_child][0], &res, sizeof(int)) != sizeof(int)) {
                res = -1;
            }
            close(c2p[idx_child][0]);
            char out[64];
            char numbuf[16];
            char pidbuf[16];
            int_to_str(pid, pidbuf);
            int_to_str(numbers[idx_child], numbuf);
            const char *msg1 = "PID ";
            const char *msg2 = " tested ";
            const char *msg3 = res == 1 ? ": prime\n" : ": not prime\n";
            int pos = 0;
            for (const char *p = msg1; *p; ++p) out[pos++] = *p;
            for (int i = 0; pidbuf[i]; ++i) out[pos++] = pidbuf[i];
            for (const char *p = msg2; *p; ++p) out[pos++] = *p;
            for (int i = 0; numbuf[i]; ++i) out[pos++] = numbuf[i];
            for (const char *p = msg3; *p; ++p) out[pos++] = *p;
            write(STDOUT_FILENO, out, pos);
        }
    }

    free(numbers); free(p2c); free(c2p); free(pids);
    return 0;
}
