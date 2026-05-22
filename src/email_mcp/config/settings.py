from __future__ import annotations

import os
from typing import TYPE_CHECKING

from email_mcp.config.constants import (
    DEFAULT_MCP_PORT,
    DEFAULT_SMTP_FROM,
    DEFAULT_SMTP_HOST,
    DEFAULT_SMTP_PORT,
    DEFAULT_SMTP_TIMEOUT,
)
from email_mcp.config.errors import ConfigError
from email_mcp.config.models import ServerSettings, Settings
from email_mcp.config.parsing import (
    compile_allowed_regex,
    empty_to_none,
    get_log_level,
    get_port,
    get_positive_float,
    get_str,
    parse_bool,
)

if TYPE_CHECKING:
    from collections.abc import Mapping


def load_server_settings(env: Mapping[str, str] | None = None) -> ServerSettings:
    """Load only the settings needed to start the MCP HTTP process."""
    source = os.environ if env is None else env
    return ServerSettings(
        mcp_port=get_port(source, "MCP_PORT", DEFAULT_MCP_PORT),
        log_level=get_log_level(source.get("LOG_LEVEL")),
        mcp_bearer_token=empty_to_none(source.get("MCP_BEARER_TOKEN")),
    )


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Load and validate all email delivery settings from environment values."""
    source = os.environ if env is None else env
    smtp_use_tls = parse_bool(source.get("SMTP_USE_TLS"), default=False)
    smtp_use_ssl = parse_bool(source.get("SMTP_USE_SSL"), default=False)
    if smtp_use_tls and smtp_use_ssl:
        msg = "SMTP_USE_TLS and SMTP_USE_SSL cannot both be true."
        raise ConfigError(msg)

    allowed_regex = empty_to_none(source.get("ALLOWED_RECIPIENT_DOMAIN_REGEX"))
    return Settings(
        smtp_host=get_str(source, "SMTP_HOST", DEFAULT_SMTP_HOST),
        smtp_port=get_port(source, "SMTP_PORT", DEFAULT_SMTP_PORT),
        smtp_username=empty_to_none(source.get("SMTP_USERNAME")),
        smtp_password=empty_to_none(source.get("SMTP_PASSWORD")),
        smtp_from=get_str(source, "SMTP_FROM", DEFAULT_SMTP_FROM),
        smtp_use_tls=smtp_use_tls,
        smtp_use_ssl=smtp_use_ssl,
        smtp_timeout=get_positive_float(source, "SMTP_TIMEOUT", DEFAULT_SMTP_TIMEOUT),
        mcp_port=get_port(source, "MCP_PORT", DEFAULT_MCP_PORT),
        log_level=get_log_level(source.get("LOG_LEVEL")),
        email_mock_mode=parse_bool(source.get("EMAIL_MOCK_MODE"), default=False),
        allowed_recipient_domain_regex=allowed_regex,
        allowed_recipient_domain_pattern=compile_allowed_regex(allowed_regex),
    )
