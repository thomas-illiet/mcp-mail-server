from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
from typing import TYPE_CHECKING, Protocol

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from email_mcp.config import Settings


class AttachmentInput(BaseModel):
    """Input schema for an email attachment passed through the MCP tool."""

    filename: str = Field(min_length=1)
    content_base64: str = Field(min_length=1)
    mime_type: str | None = None


@dataclass(frozen=True)
class ParsedAddress:
    """Parsed email address plus the recipient field where it appeared."""

    original: str
    display_name: str
    address: str
    domain: str
    field_name: str


@dataclass(frozen=True)
class PreparedEmail:
    """MIME message and SMTP envelope information ready for delivery."""

    message: EmailMessage
    envelope_recipients: list[str]
    message_id: str


@dataclass(frozen=True)
class DeliveryResult:
    """SMTP delivery result split into accepted and refused recipients."""

    accepted_recipients: list[str]
    refused_recipients: dict[str, tuple[int, bytes]]
    mocked: bool = False


@dataclass(frozen=True)
class SmtpConnectionResult:
    """Result of an SMTP connectivity check."""

    ok: bool
    smtp_host: str
    smtp_port: int
    smtp_use_tls: bool
    smtp_use_ssl: bool
    authenticated: bool
    error_type: str | None = None
    error: str | None = None


class SmtpDeliverer(Protocol):
    """Callable protocol for injecting SMTP delivery in tests."""

    def __call__(
        self,
        message: EmailMessage,
        recipients: list[str],
        settings: Settings,
    ) -> DeliveryResult:
        """Deliver a prepared email to its SMTP envelope recipients."""
        ...
