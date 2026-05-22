from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from email_mcp.mcp.context import ToolContext

if TYPE_CHECKING:
    from email_mcp.config import Settings

LOGGER = logging.getLogger(__name__)


async def log_send_start(
    ctx: ToolContext,
    *,
    to: list[str],
    cc: list[str] | None,
    bcc: list[str] | None,
    attachment_count: int,
) -> None:
    """Log the start of an email send without leaking message content."""
    await ctx.info(
        "Starting SMTP email send",
        extra={
            "to_count": len(to),
            "cc_count": len(cc or []),
            "bcc_count": len(bcc or []),
            "attachment_count": attachment_count,
        },
    )


async def log_optional_features(
    ctx: ToolContext,
    *,
    settings: Settings,
    html: str | None,
    attachment_count: int,
) -> None:
    """Log optional email features and recoverable missing features."""
    if settings.allowed_recipient_domain_pattern is None:
        await ctx.warning("Recipient domain allowlist is disabled")
    else:
        await ctx.debug("Recipient domain allowlist is enabled")

    if not html:
        await ctx.warning("Email has no HTML alternative")
    if attachment_count == 0:
        await ctx.warning("Email has no attachments")


async def log_send_failure(ctx: ToolContext, exc: Exception) -> None:
    """Log an email send failure to both the MCP client and server logs."""
    await ctx.error(
        "Email send failed",
        extra={"error_type": type(exc).__name__, "error": str(exc)},
    )
    LOGGER.exception("Email send failed")
