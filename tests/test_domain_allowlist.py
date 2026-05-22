from __future__ import annotations

import pytest

from email_mcp.config import load_settings
from email_mcp.email import EmailValidationError, prepare_email


def test_allowed_domain_regex_accepts_exact_domain() -> None:
    """Allow a recipient whose domain exactly matches the regex."""
    settings = load_settings({"ALLOWED_RECIPIENT_DOMAIN_REGEX": r"^example\.com$"})

    prepared = prepare_email(
        settings=settings,
        to=["User <user@example.com>"],
        subject="Hello",
        text="Hello",
    )

    assert prepared.envelope_recipients == ["user@example.com"]


def test_allowed_domain_regex_accepts_subdomain() -> None:
    """Allow a recipient whose subdomain matches the regex."""
    settings = load_settings({"ALLOWED_RECIPIENT_DOMAIN_REGEX": r"^(.+\.)?example\.org$"})

    prepared = prepare_email(
        settings=settings,
        to=["user@dept.example.org"],
        subject="Hello",
        text="Hello",
    )

    assert prepared.envelope_recipients == ["user@dept.example.org"]


def test_allowed_domain_regex_is_case_insensitive() -> None:
    """Match recipient domains without regard to case."""
    settings = load_settings({"ALLOWED_RECIPIENT_DOMAIN_REGEX": r"^example\.com$"})

    prepared = prepare_email(
        settings=settings,
        to=["user@Example.COM"],
        subject="Hello",
        text="Hello",
    )

    assert prepared.envelope_recipients == ["user@Example.COM"]


def test_allowed_domain_regex_rejects_blocked_domain() -> None:
    """Reject a recipient whose domain does not match the allowlist."""
    settings = load_settings({"ALLOWED_RECIPIENT_DOMAIN_REGEX": r"^example\.com$"})

    with pytest.raises(EmailValidationError, match="not allowed"):
        prepare_email(
            settings=settings,
            to=["user@blocked.test"],
            subject="Hello",
            text="Hello",
        )


def test_allowed_domain_regex_checks_to_cc_and_bcc() -> None:
    """Apply the domain allowlist to to, cc, and bcc envelope recipients."""
    settings = load_settings({"ALLOWED_RECIPIENT_DOMAIN_REGEX": r"^example\.com$"})

    with pytest.raises(EmailValidationError, match=r"blocked\.test"):
        prepare_email(
            settings=settings,
            to=["to@example.com"],
            cc=["cc@example.com"],
            bcc=["hidden@blocked.test"],
            subject="Hello",
            text="Hello",
        )
