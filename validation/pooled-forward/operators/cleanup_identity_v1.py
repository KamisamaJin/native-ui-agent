"""Content/namespace metadata checks for an exact ordinary POSIX unlink ledger.

st_blocks is an allocation observation, not stable content identity: APFS may
finish allocation/compression after a write without changing bytes or mtime.
It is retained for accounting, never used as an equality gate for deletion.
"""


def unchanged(before, after, own_unlinks):
    return (after[:5] == before[:5] and after[6:8] == before[6:8]
            and after[5] == before[5] - own_unlinks
            and (own_unlinks > 0 or after[8] == before[8]))
