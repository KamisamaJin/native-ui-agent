"""Lossless, provider-explicit native environment identifier normalization.

No locale/case guessing: only documented wire identifiers are equivalent.
Unknown values are preserved so the caller retains its original rejection policy.
"""
ENCODING = "android-compose-layout-direction-v1"

def direction(value, *, encoding):
    if encoding != ENCODING:
        raise ValueError("Unsupported direction encoding: " + str(encoding))
    aliases = {"Ltr": "ltr", "Rtl": "rtl", "ltr": "ltr", "rtl": "rtl"}
    recognized = isinstance(value, str) and value in aliases
    return {"raw": value, "canonical": aliases[value] if recognized else value,
            "recognized": recognized, "encoding": encoding}
