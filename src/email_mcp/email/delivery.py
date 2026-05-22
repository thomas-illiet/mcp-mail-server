from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import TYPE_CHECKING

from email_mcp.email.models import DeliveryResult, SmtpConnectionResult
from email_mcp.email.recipients import parse_single_address

if TYPE_CHECKING:
    from email_mcp.config import Settings


def deliver_message(
    message: EmailMessage,
    recipients: list[str],
    settings: Settings,
) -> DeliveryResult:
    """Send a prepared message through the configured SMTP server."""
    _from_name, from_address = parse_single_address(settings.smtp_from, field_name="SMTP_FROM")
    smtp_class = smtplib.SMTP_SSL if settings.smtp_use_ssl else smtplib.SMTP
    with smtp_class(settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password or "")
        refused = smtp.send_message(
            message,
            from_addr=from_address,
            to_addrs=recipients,
        )

    accepted = [recipient for recipient in recipients if recipient not in refused]
    return DeliveryResult(accepted_recipients=accepted, refused_recipients=refused)


def check_smtp_connection(settings: Settings) -> SmtpConnectionResult:
    """Open an SMTP session, optionally secure/authenticate it, and run NOOP."""
    try:
        smtp_class = smtplib.SMTP_SSL if settings.smtp_use_ssl else smtplib.SMTP
        with smtp_class(
            settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout
        ) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            authenticated = settings.smtp_username is not None
            if authenticated:
                smtp.login(settings.smtp_username or "", settings.smtp_password or "")
            smtp.noop()
    except (OSError, smtplib.SMTPException) as exc:
        return SmtpConnectionResult(
            ok=False,
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            smtp_use_tls=settings.smtp_use_tls,
            smtp_use_ssl=settings.smtp_use_ssl,
            authenticated=settings.smtp_username is not None,
            error_type=type(exc).__name__,
            error=str(exc),
        )

    return SmtpConnectionResult(
        ok=True,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_use_tls=settings.smtp_use_tls,
        smtp_use_ssl=settings.smtp_use_ssl,
        authenticated=authenticated,
    )
