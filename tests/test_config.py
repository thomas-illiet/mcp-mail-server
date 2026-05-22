from __future__ import annotations

import pytest

from email_mcp.config import (
    DEFAULT_MCP_PORT,
    DEFAULT_SMTP_FROM,
    DEFAULT_SMTP_HOST,
    DEFAULT_SMTP_PORT,
    ConfigError,
    load_server_settings,
    load_settings,
)


def test_load_settings_defaults_to_maildev() -> None:
    """Load MailDev-oriented defaults when no env values are set."""
    settings = load_settings({})

    assert settings.smtp_host == DEFAULT_SMTP_HOST
    assert settings.smtp_port == DEFAULT_SMTP_PORT
    assert settings.smtp_from == DEFAULT_SMTP_FROM
    assert settings.mcp_port == DEFAULT_MCP_PORT
    assert settings.smtp_use_tls is False
    assert settings.smtp_use_ssl is False
    assert settings.email_mock_mode is False
    assert settings.allowed_recipient_domain_pattern is None


def test_load_settings_rejects_tls_and_ssl_together() -> None:
    """Reject mutually exclusive TLS and SSL SMTP modes."""
    with pytest.raises(ConfigError, match="cannot both be true"):
        load_settings({"SMTP_USE_TLS": "true", "SMTP_USE_SSL": "1"})


def test_load_settings_reads_email_mock_mode() -> None:
    """Read the optional mock mode flag from environment values."""
    settings = load_settings({"EMAIL_MOCK_MODE": "true"})

    assert settings.email_mock_mode is True


def test_load_settings_compiles_allowed_domain_regex() -> None:
    """Compile the optional recipient domain allowlist regex."""
    settings = load_settings({"ALLOWED_RECIPIENT_DOMAIN_REGEX": r"^(example\.com)$"})

    assert settings.allowed_recipient_domain_pattern is not None
    assert settings.allowed_recipient_domain_pattern.fullmatch("EXAMPLE.COM") is not None


def test_load_settings_rejects_invalid_allowed_domain_regex() -> None:
    """Reject an invalid recipient domain allowlist regex."""
    with pytest.raises(ConfigError, match="ALLOWED_RECIPIENT_DOMAIN_REGEX is invalid"):
        load_settings({"ALLOWED_RECIPIENT_DOMAIN_REGEX": "["})


def test_load_settings_rejects_invalid_log_level() -> None:
    """Reject unsupported Python log level names."""
    with pytest.raises(ConfigError, match="LOG_LEVEL"):
        load_settings({"LOG_LEVEL": "chatty"})


def test_load_server_settings_does_not_validate_email_settings() -> None:
    """Load server settings without validating email-only configuration."""
    settings = load_server_settings({"ALLOWED_RECIPIENT_DOMAIN_REGEX": "["})

    assert settings.mcp_port == DEFAULT_MCP_PORT
    assert settings.mcp_bearer_token is None


def test_load_server_settings_reads_mcp_bearer_token() -> None:
    """Read the optional MCP bearer token from server environment values."""
    settings = load_server_settings({"MCP_BEARER_TOKEN": "local-secret"})

    assert settings.mcp_bearer_token == "local-secret"  # noqa: S105
