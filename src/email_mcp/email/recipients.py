from __future__ import annotations

from email.utils import formataddr, parseaddr

from email_mcp.email.errors import EmailValidationError
from email_mcp.email.models import ParsedAddress


def parse_recipients(values: list[str], *, field_name: str) -> list[ParsedAddress]:
    """Parse and validate a list of recipient email addresses."""
    return [parse_address(value, field_name=field_name) for value in values if value.strip()]


def parse_address(value: str, *, field_name: str) -> ParsedAddress:
    """Parse one recipient address and extract its normalized domain."""
    display_name, address = parse_single_address(value, field_name=field_name)
    domain = address.rsplit("@", maxsplit=1)[1].lower()
    return ParsedAddress(
        original=value,
        display_name=display_name,
        address=address,
        domain=domain,
        field_name=field_name,
    )


def parse_single_address(value: str, *, field_name: str) -> tuple[str, str]:
    """Parse and validate a single email address string."""
    display_name, address = parseaddr(value)
    if not address or "@" not in address:
        msg = f"{field_name} contains an invalid email address."
        raise EmailValidationError(msg)
    local_part, domain = address.rsplit("@", maxsplit=1)
    if not local_part or not domain:
        msg = f"{field_name} contains an invalid email address."
        raise EmailValidationError(msg)
    return display_name, address


def format_address(display_name: str, address: str) -> str:
    """Format an email address for use in a MIME header."""
    if display_name:
        return formataddr((display_name, address))
    return address


def format_header_addresses(recipients: list[ParsedAddress]) -> str:
    """Format parsed recipients as a comma-separated MIME header."""
    return ", ".join(
        format_address(recipient.display_name, recipient.address) for recipient in recipients
    )
