from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

CHART_PATH = Path("charts/email-mcp")


def helm_available() -> bool:
    """Return whether the Helm CLI is available for chart tests."""
    return shutil.which("helm") is not None


def helm_binary() -> str:
    """Return the resolved Helm executable path."""
    binary = shutil.which("helm")
    if binary is None:
        message = "helm CLI is not installed"
        raise RuntimeError(message)
    return binary


@pytest.mark.skipif(not helm_available(), reason="helm CLI is not installed")
def test_helm_lint_passes() -> None:
    """Verify the Helm chart passes helm lint."""
    subprocess.run([helm_binary(), "lint", str(CHART_PATH)], check=True)  # noqa: S603


@pytest.mark.skipif(not helm_available(), reason="helm CLI is not installed")
def test_helm_template_contains_rootless_readonly_deployment() -> None:
    """Verify the rendered Deployment keeps the hardened runtime settings."""
    result = subprocess.run(  # noqa: S603
        [helm_binary(), "template", "email-mcp", str(CHART_PATH)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "replicas: 1" in result.stdout
    assert "runAsUser: 1000" in result.stdout
    assert "runAsGroup: 1000" in result.stdout
    assert "readOnlyRootFilesystem: true" in result.stdout
    assert "cpu: 100m" in result.stdout
    assert "memory: 512Mi" in result.stdout
    assert "MCP_BEARER_TOKEN" in result.stdout
    assert "path: /health" in result.stdout


@pytest.mark.skipif(not helm_available(), reason="helm CLI is not installed")
def test_helm_template_can_render_ingress() -> None:
    """Verify the chart renders a Kubernetes Ingress when enabled."""
    result = subprocess.run(  # noqa: S603
        [
            helm_binary(),
            "template",
            "email-mcp",
            str(CHART_PATH),
            "--set",
            "ingress.enabled=true",
            "--set",
            "ingress.hosts[0].host=email-mcp.example.com",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "kind: Ingress" in result.stdout
    assert 'host: "email-mcp.example.com"' in result.stdout


@pytest.mark.skipif(not helm_available(), reason="helm CLI is not installed")
def test_helm_template_requires_existing_secret_name() -> None:
    """Verify disabling Secret creation requires an existing Secret name."""
    result = subprocess.run(  # noqa: S603
        [
            helm_binary(),
            "template",
            "email-mcp",
            str(CHART_PATH),
            "--set",
            "secret.create=false",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "secret.name is required" in result.stderr
