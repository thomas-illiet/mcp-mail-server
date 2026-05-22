from __future__ import annotations

import base64
import binascii
import mimetypes

from email_mcp.email.errors import EmailValidationError
from email_mcp.email.models import AttachmentInput


def decode_attachment(attachment: AttachmentInput) -> tuple[bytes, str, str]:
    """Decode a base64 attachment and resolve its MIME maintype and subtype."""
    try:
        payload = base64.b64decode(attachment.content_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        msg = f"Attachment {attachment.filename!r} is not valid base64."
        raise EmailValidationError(msg) from exc

    mime_type = attachment.mime_type or mimetypes.guess_type(attachment.filename)[0]
    if not mime_type or "/" not in mime_type:
        return payload, "application", "octet-stream"
    maintype, subtype = mime_type.split("/", maxsplit=1)
    return payload, maintype, subtype
