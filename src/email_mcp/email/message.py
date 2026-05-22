from __future__ import annotations

from email.message import EmailMessage
from email.utils import make_msgid
from typing import TYPE_CHECKING

from email_mcp.email.attachments import decode_attachment
from email_mcp.email.domain_policy import validate_allowed_domains
from email_mcp.email.errors import EmailValidationError
from email_mcp.email.models import AttachmentInput, PreparedEmail
from email_mcp.email.recipients import (
    format_address,
    format_header_addresses,
    parse_recipients,
    parse_single_address,
)

if TYPE_CHECKING:
    from email_mcp.config import Settings


def prepare_email(
    *,
    settings: Settings,
    to: list[str],
    subject: str,
    text: str,
    html: str | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    reply_to: str | None = None,
    attachments: list[AttachmentInput] | None = None,
) -> PreparedEmail:
    """Build a validated MIME email and its SMTP envelope recipients."""
    to_addresses = parse_recipients(to, field_name="to")
    cc_addresses = parse_recipients(cc or [], field_name="cc")
    bcc_addresses = parse_recipients(bcc or [], field_name="bcc")
    all_recipients = [*to_addresses, *cc_addresses, *bcc_addresses]
    if not to_addresses:
        msg = "At least one 'to' recipient is required."
        raise EmailValidationError(msg)

    validate_allowed_domains(all_recipients, settings)

    from_name, from_address = parse_single_address(settings.smtp_from, field_name="SMTP_FROM")
    message_id = make_msgid(domain=from_address.rsplit("@", maxsplit=1)[1])
    message = EmailMessage()
    message["From"] = format_address(from_name, from_address)
    message["To"] = format_header_addresses(to_addresses)
    if cc_addresses:
        message["Cc"] = format_header_addresses(cc_addresses)
    if reply_to:
        reply_name, reply_address = parse_single_address(reply_to, field_name="reply_to")
        message["Reply-To"] = format_address(reply_name, reply_address)
    message["Subject"] = subject
    message["Message-ID"] = message_id

    message.set_content(text)
    if html:
        message.add_alternative(html, subtype="html")

    for attachment in attachments or []:
        payload, maintype, subtype = decode_attachment(attachment)
        message.add_attachment(
            payload,
            maintype=maintype,
            subtype=subtype,
            filename=attachment.filename,
        )

    return PreparedEmail(
        message=message,
        envelope_recipients=[recipient.address for recipient in all_recipients],
        message_id=message_id,
    )
