from __future__ import annotations

from typing import TYPE_CHECKING

from email_mcp.email.errors import EmailValidationError
from email_mcp.email.models import ParsedAddress

if TYPE_CHECKING:
    from email_mcp.config import Settings


def validate_allowed_domains(recipients: list[ParsedAddress], settings: Settings) -> None:
    """Ensure every envelope recipient domain matches the configured allowlist regex."""
    pattern = settings.allowed_recipient_domain_pattern
    if pattern is None:
        return
    refused_domains = sorted(
        {
            recipient.domain
            for recipient in recipients
            if pattern.fullmatch(recipient.domain) is None
        },
    )
    if refused_domains:
        joined_domains = ", ".join(refused_domains)
        msg = f"Recipient domain is not allowed: {joined_domains}."
        raise EmailValidationError(msg)
