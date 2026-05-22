from __future__ import annotations

from email_mcp.config import ConfigError
from email_mcp.email import EmailValidationError
from email_mcp.mcp.server import prometheus_metrics
from email_mcp.observability import (
    classify_send_exception,
    metrics_content_type,
    record_send_attempt,
    record_send_result,
    render_metrics,
)


def test_prometheus_metrics_include_email_kpis() -> None:
    """Verify the Prometheus payload includes email-specific KPI metrics."""
    record_send_attempt(mode="test", recipient_count=2, attachment_count=1)
    record_send_result(mode="test", result="success", duration_seconds=0.01)

    payload = render_metrics().decode()

    assert 'email_mcp_email_send_attempts_total{mode="test"}' in payload
    assert 'email_mcp_email_send_results_total{mode="test",result="success"}' in payload
    assert "email_mcp_email_send_duration_seconds_bucket" in payload
    assert "email_mcp_email_recipients_per_send_bucket" in payload
    assert "email_mcp_email_attachments_per_send_bucket" in payload


def test_classify_send_exception_uses_stable_labels() -> None:
    """Verify exceptions map to low-cardinality Prometheus result labels."""
    assert classify_send_exception(ConfigError("bad config")) == "config_error"
    assert classify_send_exception(EmailValidationError("bad email")) == "validation_error"
    assert classify_send_exception(OSError("network")) == "network_error"
    assert classify_send_exception(RuntimeError("boom")) == "unexpected_error"


async def test_prometheus_metrics_endpoint_returns_text_payload() -> None:
    """Verify the FastMCP custom /metrics route returns Prometheus text."""
    response = await prometheus_metrics(None)

    assert response.media_type == metrics_content_type()
    assert b"email_mcp_email_send_attempts" in response.body
