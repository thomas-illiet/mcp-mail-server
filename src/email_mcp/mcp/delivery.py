from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from email_mcp.email import DeliveryResult, PreparedEmail, SmtpDeliverer
from email_mcp.mcp.context import ToolContext

if TYPE_CHECKING:
    from email_mcp.config import Settings

LOGGER = logging.getLogger(__name__)


async def deliver_with_progress(
    *,
    ctx: ToolContext,
    prepared: PreparedEmail,
    settings: Settings,
    deliverer: SmtpDeliverer,
) -> DeliveryResult:
    """Deliver a prepared email and report SMTP connection/send progress."""
    if settings.email_mock_mode:
        return await mock_delivery_with_progress(ctx=ctx, prepared=prepared)

    await ctx.info(
        "Opening SMTP connection",
        extra={
            "smtp_host": settings.smtp_host,
            "smtp_port": settings.smtp_port,
            "smtp_use_tls": settings.smtp_use_tls,
            "smtp_use_ssl": settings.smtp_use_ssl,
        },
    )
    await ctx.report_progress(80, total=100, message="Opening SMTP connection")
    result = await asyncio.to_thread(
        deliverer,
        prepared.message,
        prepared.envelope_recipients,
        settings,
    )
    await ctx.report_progress(95, total=100, message="Email sent")
    return result


async def mock_delivery_with_progress(
    *,
    ctx: ToolContext,
    prepared: PreparedEmail,
) -> DeliveryResult:
    """Pretend to deliver an email without opening an SMTP connection."""
    await ctx.report_progress(80, total=100, message="Processing delivery")
    await ctx.report_progress(95, total=100, message="Email accepted")
    return DeliveryResult(
        accepted_recipients=prepared.envelope_recipients,
        refused_recipients={},
        mocked=True,
    )


async def finish_success(
    *,
    ctx: ToolContext,
    message_id: str,
    result: DeliveryResult,
) -> dict[str, Any]:
    """Build the success response and emit final logs and progress."""
    response = build_response(message_id, result)
    await ctx.info(
        "SMTP email accepted",
        extra={"accepted_count": len(result.accepted_recipients)},
    )
    await ctx.report_progress(100, total=100, message="Done")
    LOGGER.info(
        "SMTP email accepted by server",
        extra={"accepted_count": len(result.accepted_recipients)},
    )
    return response


def build_response(message_id: str, result: DeliveryResult) -> dict[str, Any]:
    """Convert the SMTP delivery result into the MCP tool response payload."""
    return {
        "ok": True,
        "message_id": message_id,
        "accepted_recipients": result.accepted_recipients,
    }
