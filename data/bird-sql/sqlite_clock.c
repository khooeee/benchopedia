#include <sys/time.h>

/* SQLite 3.40.1's Unix VFS gets SQL wall-clock time through gettimeofday.
 * Leave clock_gettime intact so the worker measures real elapsed time. */
int gettimeofday(struct timeval *time, void *zone)
{
    (void)zone;
    time->tv_sec = 1762387200; /* 2025-11-06 00:00:00 UTC, split release */
    time->tv_usec = 0;
    return 0;
}
