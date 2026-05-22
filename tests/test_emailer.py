from __future__ import annotations

import base64

import pytest

from email_mcp.config import load_settings
from email_mcp.email import (
    AttachmentInput,
    EmailValidationError,
    decode_attachment,
    prepare_email,
)


def test_prepare_email_with_text_only() -> None:
    """Build a basic text-only email."""
    settings = load_settings({})

    prepared = prepare_email(
        settings=settings,
        to=["user@example.com"],
        subject="Hello",
        text="Plain body",
    )

    assert prepared.message["To"] == "user@example.com"
    assert prepared.message["Subject"] == "Hello"
    assert prepared.message.get_body(preferencelist=("plain",)).get_content() == "Plain body\n"


def test_prepare_email_with_html_alternative() -> None:
    """Build an email with both plain text and HTML parts."""
    settings = load_settings({})

    prepared = prepare_email(
        settings=settings,
        to=["user@example.com"],
        subject="Hello",
        text="Plain body",
        html="<p>HTML body</p>",
    )

    assert prepared.message.get_body(preferencelist=("html",)).get_content() == "<p>HTML body</p>\n"


def test_prepare_email_with_cc_bcc_and_reply_to() -> None:
    """Build headers while keeping BCC only in the SMTP envelope."""
    settings = load_settings({})

    prepared = prepare_email(
        settings=settings,
        to=["to@example.com"],
        cc=["cc@example.com"],
        bcc=["hidden@example.com"],
        reply_to="reply@example.com",
        subject="Hello",
        text="Plain body",
    )

    assert prepared.message["Cc"] == "cc@example.com"
    assert prepared.message["Reply-To"] == "reply@example.com"
    assert "Bcc" not in prepared.message
    assert prepared.envelope_recipients == [
        "to@example.com",
        "cc@example.com",
        "hidden@example.com",
    ]


def test_prepare_email_with_attachment() -> None:
    """Attach a base64 payload to the generated email."""
    settings = load_settings({})
    content = base64.b64encode(b"hello attachment").decode()

    prepared = prepare_email(
        settings=settings,
        to=["user@example.com"],
        subject="Hello",
        text="Plain body",
        attachments=[AttachmentInput(filename="hello.txt", content_base64=content)],
    )

    attachments = list(prepared.message.iter_attachments())
    assert len(attachments) == 1
    assert attachments[0].get_filename() == "hello.txt"
    assert attachments[0].get_content() == "hello attachment"


def test_decode_attachment_rejects_invalid_base64() -> None:
    """Reject an attachment whose content is not valid base64."""
    attachment = AttachmentInput(filename="bad.txt", content_base64="not base64")

    with pytest.raises(EmailValidationError, match="valid base64"):
        decode_attachment(attachment)


def test_prepare_email_requires_to_recipient() -> None:
    """Reject emails with no primary recipient."""
    settings = load_settings({})

    with pytest.raises(EmailValidationError, match="At least one"):
        prepare_email(settings=settings, to=[], subject="Hello", text="Plain body")
