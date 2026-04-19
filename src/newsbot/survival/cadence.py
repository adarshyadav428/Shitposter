from __future__ import annotations

import random
from datetime import timedelta


def next_delay_seconds(avg_posts_per_day: float) -> int:
    if avg_posts_per_day <= 0:
        return 24 * 3600
    lam = avg_posts_per_day / (24 * 3600)
    delay = random.expovariate(lam)
    return int(max(60, delay))


def min_gap_elapsed(seconds_since_last_post: float, min_gap_minutes: int) -> bool:
    return seconds_since_last_post >= timedelta(minutes=min_gap_minutes).total_seconds()
