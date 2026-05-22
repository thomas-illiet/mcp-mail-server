from __future__ import annotations

import smtplib

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from email_mcp.config import ConfigError
from email_mcp.email import EmailValidationError

SEND_ATTEMPTS = Counter(
    "email_mcp_email_send_attempts",
    "Number of send_email tool calls.",
    labelnames=("mode",),
)
SEND_RESULTS = Counter(
    "email_mcp_email_send_results",
    "Number of send_email outcomes by result.",
    labelnames=("mode", "result"),
)
SEND_DURATION_SECONDS = Histogram(
    "email_mcp_email_send_duration_seconds",
    "Duration of send_email calls in seconds.",
    labelnames=("mode", "result"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30),
)
RECIPIENTS_PER_SEND = Histogram(
    "email_mcp_email_recipients_per_send",
    "Number of envelope recipients per send_email call.",
    buckets=(1, 2, 3, 5, 10, 25, 50, 100),
)
ATTACHMENTS_PER_SEND = Histogram(
    "email_mcp_email_attachments_per_send",
    "Number of attachments per send_email call.",
    buckets=(0, 1, 2, 3, 5, 10, 25),
)


def delivery_mode(*, mock_mode: bool) -> str:
    """Return the low-cardinality Prometheus label for delivery mode."""
    if mock_mode:
        return "mock"
    return "smtp"


def record_send_attempt(
    *,
    mode: str,
    recipient_count: int,
    attachment_count: int,
) -> None:
    """Record a send_email attempt and its input-size KPI histograms."""
    SEND_ATTEMPTS.labels(mode=mode).inc()
    RECIPIENTS_PER_SEND.observe(recipient_count)
    ATTACHMENTS_PER_SEND.observe(attachment_count)


def record_send_result(
    *,
    mode: str,
    result: str,
    duration_seconds: float,
) -> None:
    """Record the terminal send_email result and duration."""
    SEND_RESULTS.labels(mode=mode, result=result).inc()
    SEND_DURATION_SECONDS.labels(mode=mode, result=result).observe(duration_seconds)


def classify_send_exception(exc: Exception) -> str:
    """Map internal exceptions to stable low-cardinality Prometheus labels."""
    if isinstance(exc, ConfigError):
        return "config_error"
    if isinstance(exc, EmailValidationError):
        return "validation_error"
    if isinstance(exc, smtplib.SMTPException):
        return "smtp_error"
    if isinstance(exc, OSError):
        return "network_error"
    return "unexpected_error"


def render_metrics() -> bytes:
    """Render the current Prometheus text exposition payload."""
    return generate_latest()


def metrics_content_type() -> str:
    """Return the Prometheus text exposition content type."""
    return CONTENT_TYPE_LATEST
