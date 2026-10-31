/* No filesystem, console retarget or heap is required. Telemetry uses HAL UART.
 * Explicit stubs keep newlib's optional stdio paths defined without semihosting. */
#include <errno.h>
#include <stddef.h>
#include <sys/stat.h>

#include "board.h"
int _close(int fd) {
    (void)fd;
    errno = EBADF;
    return -1;
}
int _lseek(int fd, int offset, int whence) {
    (void)fd;
    (void)offset;
    (void)whence;
    errno = ESPIPE;
    return -1;
}
int _read(int fd, char *buf, int count) {
    (void)fd;
    (void)buf;
    (void)count;
    errno = ENOSYS;
    return -1;
}
int _write(int fd, char *buf, int count) {
    (void)fd;
    (void)buf;
    (void)count;
    errno = ENOSYS;
    return -1;
}
int _fstat(int fd, struct stat *st) {
    (void)fd;
    st->st_mode = S_IFCHR;
    return 0;
}
int _isatty(int fd) { return fd >= 0 && fd <= 2; }
int _getpid(void) { return 1; }
int _kill(int pid, int sig) {
    (void)pid;
    (void)sig;
    errno = EINVAL;
    return -1;
}
void *_sbrk(ptrdiff_t increment) {
    (void)increment;
    errno = ENOMEM;
    return (void *)-1;
}
__attribute__((noreturn)) void _exit(int status) {
    Board_Fatal((uint32_t)(100 + status));
    for (;;) {
    }
}
