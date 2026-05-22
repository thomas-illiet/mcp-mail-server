from __future__ import annotations

import smtplib
import time
from typing import TYPE_CHECKING, Any

from email_mcp.config import ConfigError
from email_mcp.email import (
    AttachmentInput,
    EmailValidationError,
    SmtpDeliverer,
    deliver_message,
)
from email_mcp.mcp.client_logging import log_optional_features, log_send_failure, log_send_start
from email_mcp.mcp.context import ToolContext
from email_mcp.mcp.delivery import deliver_with_progress, finish_success
from email_mcp.mcp.message_building import build_message_with_progress
from email_mcp.observability import (
    classify_send_exception,
    delivery_mode,
    record_send_attempt,
    record_send_result,
)

if TYPE_CHECKING:
    from email_mcp.config import Settings


async def send_email_impl(
    *,
    to: list[str],
    subject: str,
    text: str,
    ctx: ToolContext,
    settings: Settings,
    html: str | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    reply_to: str | None = None,
    attachments: list[AttachmentInput] | None = None,
    deliverer: SmtpDeliverer = deliver_message,
) -> dict[str, Any]:
    """Run the full send-email workflow with progress and client logging."""
    attachment_count = len(attachments or [])
    mode = delivery_mode(mock_mode=settings.email_mock_mode)
    started_at = time.perf_counter()
    record_send_attempt(
        mode=mode,
        recipient_count=len(to) + len(cc or []) + len(bcc or []),
        attachment_count=attachment_count,
    )
    await log_send_start(ctx, to=to, cc=cc, bcc=bcc, attachment_count=attachment_count)
    await ctx.report_progress(5, total=100, message="Configuration loaded")
    await log_optional_features(
        ctx,
        settings=settings,
        html=html,
        attachment_count=attachment_count,
    )

    try:
        prepared = await build_message_with_progress(
            ctx=ctx,
            settings=settings,
            to=to,
            subject=subject,
            text=text,
            html=html,
            cc=cc,
            bcc=bcc,
            reply_to=reply_to,
            attachments=attachments or [],
        )
        result = await deliver_with_progress(
            ctx=ctx,
            prepared=prepared,
            settings=settings,
            deliverer=deliverer,
        )
        record_send_result(
            mode=mode,
            result="success",
            duration_seconds=time.perf_counter() - started_at,
        )
        return await finish_success(ctx=ctx, message_id=prepared.message_id, result=result)
    except (ConfigError, EmailValidationError, OSError, smtplib.SMTPException) as exc:
        record_send_result(
            mode=mode,
            result=classify_send_exception(exc),
            duration_seconds=time.perf_counter() - started_at,
        )
        await log_send_failure(ctx, exc)
        raise
