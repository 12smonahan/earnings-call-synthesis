"""Environment variable helpers."""

from __future__ import annotations

import os


def get_int_env(name: str, default: int | str) -> int:
    """Return an integer from an environment variable with a safe fallback.

    Treats unset or blank values as the provided ``default`` and raises a
    descriptive ``ValueError`` when the value cannot be parsed as an integer.
    """

    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return int(default)

    try:
        return int(raw)
    except ValueError as exc:  # pragma: no cover - simple guard clause
        raise ValueError(f"{name} must be an integer (got {raw!r})") from exc
