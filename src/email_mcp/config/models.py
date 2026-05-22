from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime settings used when sending an email."""

    smtp_host: str
    smtp_port: int
    smtp_username: str | None
    smtp_password: str | None
    smtp_from: str
    smtp_use_tls: bool
    smtp_use_ssl: bool
    smtp_timeout: float
    mcp_port: int
    log_level: str
    email_mock_mode: bool
    allowed_recipient_domain_regex: str | None
    allowed_recipient_domain_pattern: re.Pattern[str] | None


@dataclass(frozen=True)
class ServerSettings:
    """Minimal settings required to start the MCP HTTP server."""

    mcp_port: int
    log_level: str
    mcp_bearer_token: str | None
