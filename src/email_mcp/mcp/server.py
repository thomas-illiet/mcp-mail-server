from __future__ import annotations

import asyncio
from dataclasses import asdict
from typing import TYPE_CHECKING, Any

from fastmcp import Context, FastMCP
from starlette.responses import JSONResponse, Response

from email_mcp.config import (
    ConfigError,
    configure_python_logging,
    load_server_settings,
    load_settings,
)
from email_mcp.email import AttachmentInput, check_smtp_connection, deliver_message
from email_mcp.mcp.auth import load_bearer_auth_provider
from email_mcp.mcp.workflow import send_email_impl
from email_mcp.observability import (
    metrics_content_type,
    record_send_attempt,
    record_send_result,
    render_metrics,
)

if TYPE_CHECKING:
    from starlette.requests import Request

mcp = FastMCP("Email MCP Server", auth=load_bearer_auth_provider())


@mcp.custom_route("/metrics", methods=["GET"], include_in_schema=False)
async def prometheus_metrics(_request: Request) -> Response:
    """Expose Prometheus metrics for scraping."""
    return Response(render_metrics(), media_type=metrics_content_type())


@mcp.custom_route("/health", methods=["GET"], include_in_schema=False)
async def health(_request: Request) -> JSONResponse:
    """Expose an HTTP health check that validates SMTP connectivity."""
    payload = await run_smtp_connection_test()
    status_code = 200 if payload["ok"] else 503
    return JSONResponse(payload, status_code=status_code)


@mcp.tool
async def send_email(
    to: list[str],
    subject: str,
    text: str,
    ctx: Context,
    html: str | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    reply_to: str | None = None,
    attachments: list[AttachmentInput] | None = None,
) -> dict[str, Any]:
    """Send an email through the configured SMTP server."""
    try:
        settings = load_settings()
    except ConfigError as exc:
        record_send_attempt(
            mode="unknown",
            recipient_count=len(to) + len(cc or []) + len(bcc or []),
            attachment_count=len(attachments or []),
        )
        record_send_result(mode="unknown", result="config_error", duration_seconds=0.0)
        await ctx.error(
            "Invalid email MCP configuration",
            extra={"error_type": type(exc).__name__, "error": str(exc)},
        )
        raise

    return await send_email_impl(
        to=to,
        subject=subject,
        text=text,
        ctx=ctx,
        settings=settings,
        html=html,
        cc=cc,
        bcc=bcc,
        reply_to=reply_to,
        attachments=attachments,
        deliverer=deliver_message,
    )


@mcp.tool
async def test_smtp_connection(ctx: Context) -> dict[str, Any]:
    """Test the configured SMTP connection without sending an email."""
    payload = await run_smtp_connection_test()
    if payload["ok"]:
        await ctx.info("SMTP connection test succeeded", extra=safe_smtp_log_extra(payload))
    else:
        await ctx.error("SMTP connection test failed", extra=safe_smtp_log_extra(payload))
    return payload


async def run_smtp_connection_test() -> dict[str, Any]:
    """Load SMTP settings and run the shared SMTP connectivity check."""
    try:
        settings = load_settings()
    except ConfigError as exc:
        return {
            "ok": False,
            "smtp_host": None,
            "smtp_port": None,
            "smtp_use_tls": None,
            "smtp_use_ssl": None,
            "authenticated": None,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    result = await asyncio.to_thread(check_smtp_connection, settings)
    return asdict(result)


def safe_smtp_log_extra(payload: dict[str, Any]) -> dict[str, Any]:
    """Return non-sensitive SMTP connection fields suitable for logs."""
    return {
        "ok": payload["ok"],
        "smtp_host": payload["smtp_host"],
        "smtp_port": payload["smtp_port"],
        "smtp_use_tls": payload["smtp_use_tls"],
        "smtp_use_ssl": payload["smtp_use_ssl"],
        "authenticated": payload["authenticated"],
        "error_type": payload["error_type"],
    }


def main() -> None:
    """Start the FastMCP HTTP server with process-level settings."""
    settings = load_server_settings()
    configure_python_logging(settings.log_level)
    mcp.run(transport="http", host="0.0.0.0", port=settings.mcp_port)  # noqa: S104
