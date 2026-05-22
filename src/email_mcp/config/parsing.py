from __future__ import annotations

import re
from typing import TYPE_CHECKING

from email_mcp.config.constants import DEFAULT_LOG_LEVEL, MAX_PORT
from email_mcp.config.errors import ConfigError

if TYPE_CHECKING:
    from collections.abc import Mapping


def get_str(source: Mapping[str, str], key: str, default: str) -> str:
    """Read a non-empty string setting from an environment mapping."""
    value = source.get(key, default).strip()
    if not value:
        msg = f"{key} cannot be empty."
        raise ConfigError(msg)
    return value


def get_port(source: Mapping[str, str], key: str, default: int) -> int:
    """Read and validate a TCP port from an environment mapping."""
    raw_value = source.get(key)
    if raw_value is None or not raw_value.strip():
        return default
    try:
        value = int(raw_value)
    except ValueError as exc:
        msg = f"{key} must be an integer port."
        raise ConfigError(msg) from exc
    if not 1 <= value <= MAX_PORT:
        msg = f"{key} must be between 1 and {MAX_PORT}."
        raise ConfigError(msg)
    return value


def get_positive_float(source: Mapping[str, str], key: str, default: float) -> float:
    """Read and validate a positive floating-point setting."""
    raw_value = source.get(key)
    if raw_value is None or not raw_value.strip():
        return default
    try:
        value = float(raw_value)
    except ValueError as exc:
        msg = f"{key} must be a number."
        raise ConfigError(msg) from exc
    if value <= 0:
        msg = f"{key} must be greater than 0."
        raise ConfigError(msg)
    return value


def parse_bool(value: str | None, *, default: bool) -> bool:
    """Parse a permissive environment-style boolean value."""
    if value is None or not value.strip():
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    msg = f"Invalid boolean value: {value!r}."
    raise ConfigError(msg)


def get_log_level(value: str | None) -> str:
    """Normalize and validate a Python logging level name."""
    level = (value or DEFAULT_LOG_LEVEL).strip().upper()
    valid_levels = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}
    if level not in valid_levels:
        msg = f"LOG_LEVEL must be one of: {', '.join(sorted(valid_levels))}."
        raise ConfigError(msg)
    return level


def empty_to_none(value: str | None) -> str | None:
    """Convert missing or blank environment values to None."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def compile_allowed_regex(value: str | None) -> re.Pattern[str] | None:
    """Compile the optional recipient domain allowlist regex."""
    if value is None:
        return None
    try:
        return re.compile(value, flags=re.IGNORECASE)
    except re.error as exc:
        msg = f"ALLOWED_RECIPIENT_DOMAIN_REGEX is invalid: {exc}."
        raise ConfigError(msg) from exc
