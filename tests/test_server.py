from __future__ import annotations

import base64
import importlib
import json
from typing import Any

import pytest
from fastmcp import Client

from email_mcp.config import load_settings
from email_mcp.email import (
    AttachmentInput,
    DeliveryResult,
    EmailValidationError,
    SmtpConnectionResult,
)
from email_mcp.mcp import mcp, send_email_impl

HTTP_OK = 200
HTTP_SERVICE_UNAVAILABLE = 503


class FakeContext:
    """In-memory context that records progress and log calls."""

    def __init__(self) -> None:
        """Initialize empty progress and log capture lists."""
        self.progress: list[tuple[float, float | None, str | None]] = []
        self.logs: list[tuple[str, str, dict[str, Any] | None]] = []

    async def report_progress(
        self,
        progress: float,
        total: float | None = None,
        message: str | None = None,
    ) -> None:
        """Capture one progress report call."""
        self.progress.append((progress, total, message))

    async def debug(
        self,
        message: str,
        _logger_name: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Capture one debug log call."""
        self.logs.append(("debug", message, extra))

    async def info(
        self,
        message: str,
        _logger_name: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Capture one info log call."""
        self.logs.append(("info", message, extra))

    async def warning(
        self,
        message: str,
        _logger_name: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Capture one warning log call."""
        self.logs.append(("warning", message, extra))

    async def error(
        self,
        message: str,
        _logger_name: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Capture one error log call."""
        self.logs.append(("error", message, extra))


def fake_deliverer(_message, recipients, _settings) -> DeliveryResult:
    """Return a successful SMTP delivery result without network access."""
    return DeliveryResult(accepted_recipients=list(recipients), refused_recipients={})


def failing_deliverer(_message, _recipients, _settings) -> DeliveryResult:
    """Fail if mock mode accidentally calls the SMTP deliverer."""
    message = "mock mode must not call SMTP delivery"
    raise AssertionError(message)


def fake_smtp_connection(_settings) -> SmtpConnectionResult:
    """Return a successful SMTP connectivity check without network access."""
    return SmtpConnectionResult(
        ok=True,
        smtp_host="smtp.example.test",
        smtp_port=1025,
        smtp_use_tls=False,
        smtp_use_ssl=False,
        authenticated=False,
    )


def failed_smtp_connection(_settings) -> SmtpConnectionResult:
    """Return a failed SMTP connectivity check without network access."""
    return SmtpConnectionResult(
        ok=False,
        smtp_host="smtp.example.test",
        smtp_port=1025,
        smtp_use_tls=False,
        smtp_use_ssl=False,
        authenticated=False,
        error_type="ConnectionRefusedError",
        error="connection refused",
    )


async def test_send_email_impl_reports_progress_and_logs() -> None:
    """Verify workflow progress and client logs on a successful send."""
    ctx = FakeContext()
    settings = load_settings({"ALLOWED_RECIPIENT_DOMAIN_REGEX": r"^example\.com$"})
    attachment = AttachmentInput(
        filename="hello.txt",
        content_base64=base64.b64encode(b"hello").decode(),
    )

    response = await send_email_impl(
        to=["user@example.com"],
        cc=[],
        bcc=[],
        subject="Hello",
        text="Plain body",
        html="<p>HTML body</p>",
        attachments=[attachment],
        ctx=ctx,
        settings=settings,
        deliverer=fake_deliverer,
    )

    assert response["ok"] is True
    assert response["mock"] is False
    assert [entry[0] for entry in ctx.progress] == [5, 15, 30, 70, 80, 95, 100]
    assert {"debug", "info"}.issubset({entry[0] for entry in ctx.logs})
    assert not any("content_base64" in str(entry[2]) for entry in ctx.logs)


async def test_send_email_impl_logs_validation_errors() -> None:
    """Verify validation failures are logged at error level."""
    ctx = FakeContext()
    settings = load_settings({"ALLOWED_RECIPIENT_DOMAIN_REGEX": r"^example\.com$"})

    with pytest.raises(EmailValidationError):
        await send_email_impl(
            to=["user@blocked.test"],
            subject="Hello",
            text="Plain body",
            ctx=ctx,
            settings=settings,
            deliverer=fake_deliverer,
        )

    assert any(level == "error" for level, _message, _extra in ctx.logs)


async def test_send_email_impl_mock_mode_skips_delivery() -> None:
    """Verify mock mode validates and returns success without SMTP delivery."""
    ctx = FakeContext()
    settings = load_settings(
        {
            "ALLOWED_RECIPIENT_DOMAIN_REGEX": r"^example\.com$",
            "EMAIL_MOCK_MODE": "true",
        },
    )

    response = await send_email_impl(
        to=["user@example.com"],
        subject="Hello",
        text="Plain body",
        ctx=ctx,
        settings=settings,
        deliverer=failing_deliverer,
    )

    assert response["ok"] is True
    assert response["mock"] is True
    assert response["accepted_recipients"] == ["user@example.com"]
    assert [entry[0] for entry in ctx.progress] == [5, 15, 30, 70, 80, 95, 100]
    assert any("mock mode" in message for _level, message, _extra in ctx.logs)


async def test_mcp_tool_is_listed_and_callable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify the FastMCP tool is visible and callable in memory."""
    monkeypatch.setenv("ALLOWED_RECIPIENT_DOMAIN_REGEX", r"^example\.com$")
    server_module = importlib.import_module("email_mcp.mcp.server")
    monkeypatch.setattr(server_module, "deliver_message", fake_deliverer)

    async with Client(mcp) as client:
        tools = await client.list_tools()
        assert any(tool.name == "send_email" for tool in tools)
        assert any(tool.name == "test_smtp_connection" for tool in tools)

        result = await client.call_tool(
            "send_email",
            {
                "to": ["user@example.com"],
                "subject": "Hello",
                "text": "Plain body",
            },
        )

    assert result.structured_content is not None
    assert result.structured_content["ok"] is True
    assert result.structured_content["accepted_recipients"] == ["user@example.com"]


async def test_smtp_connection_tool_is_callable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify the SMTP connection test MCP tool returns connection status."""
    server_module = importlib.import_module("email_mcp.mcp.server")
    monkeypatch.setattr(server_module, "check_smtp_connection", fake_smtp_connection)

    async with Client(mcp) as client:
        result = await client.call_tool("test_smtp_connection", {})

    assert result.structured_content is not None
    assert result.structured_content["ok"] is True
    assert result.structured_content["smtp_host"] == "smtp.example.test"


async def test_health_endpoint_returns_200_on_smtp_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify /health returns HTTP 200 when SMTP connectivity succeeds."""
    server_module = importlib.import_module("email_mcp.mcp.server")
    monkeypatch.setattr(server_module, "check_smtp_connection", fake_smtp_connection)

    response = await server_module.health(None)
    payload = json.loads(response.body)

    assert response.status_code == HTTP_OK
    assert payload["ok"] is True


async def test_health_endpoint_returns_503_on_smtp_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify /health returns HTTP 503 when SMTP connectivity fails."""
    server_module = importlib.import_module("email_mcp.mcp.server")
    monkeypatch.setattr(server_module, "check_smtp_connection", failed_smtp_connection)

    response = await server_module.health(None)
    payload = json.loads(response.body)

    assert response.status_code == HTTP_SERVICE_UNAVAILABLE
    assert payload["ok"] is False
    assert payload["error_type"] == "ConnectionRefusedError"
