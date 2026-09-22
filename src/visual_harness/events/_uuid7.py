"""UUIDv7 (RFC 9562): ID de evento cronologicamente ordenável (TechSpecs
Seção 8). Implementado à mão porque este projeto roda em Python 3.12 e
`uuid.uuid7` só chega na stdlib no 3.14.
"""
import os
import time
import uuid


def uuid7() -> uuid.UUID:
    unix_ts_ms = int(time.time() * 1000)
    rand_a = int.from_bytes(os.urandom(2), "big") & 0x0FFF
    rand_b = int.from_bytes(os.urandom(8), "big") & 0x3FFFFFFFFFFFFFFF

    value = unix_ts_ms << 80
    value |= 0x7 << 76
    value |= rand_a << 64
    value |= 0b10 << 62
    value |= rand_b

    return uuid.UUID(int=value)
