#!/usr/bin/env python3
"""Measure CLOCK_REALTIME - CLOCK_MONOTONIC (ns) in this process (used by run_trace.sh).

Reads MONOTONIC, REALTIME, MONOTONIC back to back 2000 times and keeps the read with the
narrowest monotonic bracket: offset = realtime - midpoint(monotonic), half-width = bound on the
error of that single pair.  Prints key=value lines.  Stdlib only.
"""
import time

best = None
for _ in range(2000):
    m1 = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
    r = time.clock_gettime_ns(time.CLOCK_REALTIME)
    m2 = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
    w = m2 - m1
    if best is None or w < best[0]:
        best = (w, r - (m1 + m2) // 2, r)
print(f"offset_ns={best[1]}")
print(f"halfwidth_ns={best[0] / 2:.0f}")
print(f"realtime_ns={best[2]}")
