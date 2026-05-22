from __future__ import annotations

from pathlib import Path

import yaml


def test_dockerfile_runs_as_appuser_uid_1000() -> None:
    """Verify the runtime image uses the non-root appuser account."""
    dockerfile = Path("Dockerfile").read_text()

    assert "appuser" in dockerfile
    assert "--uid 1000" in dockerfile
    assert "USER 1000:1000" in dockerfile


def test_dockerfile_does_not_use_uv_at_runtime() -> None:
    """Verify runtime execution uses the installed venv entrypoint directly."""
    dockerfile = Path("Dockerfile").read_text()

    assert 'CMD ["/app/.venv/bin/email-mcp"]' in dockerfile
    assert 'CMD ["uv", "run"' not in dockerfile


def test_compose_uses_read_only_rootless_service() -> None:
    """Verify Docker Compose mirrors the intended OpenShift hardening."""
    compose = yaml.safe_load(Path("compose.yaml").read_text())
    service = compose["services"]["mcp-email-server"]

    assert service["user"] == "1000:1000"
    assert service["read_only"] is True
    assert "/tmp:size=64m,mode=1777" in service["tmpfs"]  # noqa: S108
    assert service["cap_drop"] == ["ALL"]
