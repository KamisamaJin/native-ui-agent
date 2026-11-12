"""Explicit shared-process clocks and append-only corrections of old episodes.

CPython 3.9/macOS process-relative time.monotonic() cannot time two CLI runs.
No native/SUT clock, source window, earlier record or denominator is changed.
"""
import math
import os
import time


BASIS = 'clock_gettime(CLOCK_MONOTONIC)'


def point(prefix):
    before = time.clock_gettime(time.CLOCK_MONOTONIC)
    unix = time.time()
    process_relative = time.monotonic()
    after = time.clock_gettime(time.CLOCK_MONOTONIC)
    return {prefix + '_at_unix': unix,
            prefix + '_at_clock_gettime': after,
            prefix + '_at_monotonic': process_relative,
            prefix + '_shared_clock_bounds': [before, after],
            prefix + '_process_id': os.getpid(), 'shared_clock_basis': BASIS}


def finite(value):
    return type(value) in {int, float} and math.isfinite(value)


def interval(start, end):
    """Prefer recorded kernel endpoints; otherwise use recorded Unix endpoints.

    A Unix fallback is labeled, never represented as an observed kernel time.
    A negative interval is a failure, not a zero duration. Raw process-relative
    differences are retained as noncomparable diagnostics, never the cost.
    """
    a, b = start.get('started_at_unix'), end.get('finished_at_unix')
    if not finite(a) or not finite(b) or b < a:
        raise ValueError('Valid ordered original Unix episode endpoints required')
    unix = b - a
    first, last = start.get('started_at_clock_gettime'), end.get('finished_at_clock_gettime')
    if first is not None and last is not None:
        if (start.get('shared_clock_basis') != BASIS or end.get('shared_clock_basis') != BASIS
                or not finite(first) or not finite(last) or last < first):
            raise ValueError('Recorded shared clock endpoints are inconsistent')
        duration = last - first
        basis = BASIS
        limitation = None
    else:
        duration = unix
        basis = 'recorded Unix endpoints; original shared endpoints unavailable'
        limitation = 'Wall-clock fallback assumes no intervening system-clock jump; process-relative monotonic values are not cross-process duration evidence.'
    raw_first, raw_last = start.get('started_at_monotonic'), end.get('finished_at_monotonic')
    return {'wall_seconds': duration, 'wall_clock_basis': basis,
            'unix_wall_seconds': unix, 'shared_minus_unix_seconds': duration - unix,
            'raw_process_monotonic_delta_not_comparable': raw_last - raw_first if finite(raw_first) and finite(raw_last) else None,
            'original_reported_wall_seconds': end.get('wall_seconds'),
            'limitation': limitation}
