from __future__ import annotations

from typing import TYPE_CHECKING

from email_mcp.email import AttachmentInput, PreparedEmail, decode_attachment, prepare_email
from email_mcp.mcp.context import ToolContext

if TYPE_CHECKING:
    from email.message import EmailMessage

    from email_mcp.config import Settings


async def build_message_with_progress(
    *,
    ctx: ToolContext,
    settings: Settings,
    to: list[str],
    subject: str,
    text: str,
    html: str | None,
    cc: list[str] | None,
    bcc: list[str] | None,
    reply_to: str | None,
    attachments: list[AttachmentInput],
) -> PreparedEmail:
    """Build the MIME message while reporting validation and attachment progress."""
    await ctx.debug("Validating recipients and allowed domains")
    prepared = prepare_email(
        settings=settings,
        to=to,
        subject=subject,
        text=text,
        html=html,
        cc=cc,
        bcc=bcc,
        reply_to=reply_to,
        attachments=[],
    )
    await ctx.report_progress(15, total=100, message="Recipients validated")

    await ctx.debug("Building email body")
    await ctx.report_progress(30, total=100, message="Email body built")

    return await attach_files_with_progress(
        base_message=prepared.message,
        envelope_recipients=prepared.envelope_recipients,
        message_id=prepared.message_id,
        attachments=attachments,
        ctx=ctx,
    )


async def attach_files_with_progress(
    *,
    base_message: EmailMessage,
    envelope_recipients: list[str],
    message_id: str,
    attachments: list[AttachmentInput],
    ctx: ToolContext,
) -> PreparedEmail:
    """Attach files to a MIME message and report proportional progress."""
    for index, attachment in enumerate(attachments, start=1):
        payload, maintype, subtype = decode_attachment(attachment)
        base_message.add_attachment(
            payload,
            maintype=maintype,
            subtype=subtype,
            filename=attachment.filename,
        )
        progress = 30 + (40 * index / len(attachments))
        await ctx.report_progress(
            progress=progress,
            total=100,
            message=f"Attachment {index}/{len(attachments)} processed",
        )
    if not attachments:
        await ctx.report_progress(70, total=100, message="No attachments to process")
    return PreparedEmail(
        message=base_message,
        envelope_recipients=envelope_recipients,
        message_id=message_id,
    )
