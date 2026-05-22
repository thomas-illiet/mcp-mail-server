from __future__ import annotations

import httpx
from fastmcp import FastMCP

from email_mcp.mcp.auth import (
    build_bearer_auth_provider,
    get_mcp_bearer_token,
    load_bearer_auth_provider,
)

HTTP_UNAUTHORIZED = 401


def test_get_mcp_bearer_token_treats_blank_values_as_disabled() -> None:
    """Verify missing or blank MCP bearer tokens disable authentication."""
    assert get_mcp_bearer_token({}) is None
    assert get_mcp_bearer_token({"MCP_BEARER_TOKEN": "   "}) is None


def test_load_bearer_auth_provider_reads_environment_token(
    monkeypatch,
) -> None:
    """Verify the optional FastMCP auth provider is created from environment values."""
    monkeypatch.setenv("MCP_BEARER_TOKEN", "local-secret")

    provider = load_bearer_auth_provider()

    assert provider is not None


async def test_bearer_auth_provider_accepts_only_configured_token() -> None:
    """Verify the bearer auth provider accepts only the configured token."""
    provider = build_bearer_auth_provider("local-secret")

    assert provider is not None
    assert await provider.verify_token("wrong-secret") is None

    access_token = await provider.verify_token("local-secret")

    assert access_token is not None
    assert access_token.client_id == "email-mcp-env-token"


async def test_bearer_auth_provider_protects_fastmcp_http_endpoint() -> None:
    """Verify FastMCP rejects MCP HTTP requests without the configured bearer token."""
    provider = build_bearer_auth_provider("local-secret")
    test_mcp = FastMCP("auth-test", auth=provider)
    app = test_mcp.http_app(path="/mcp")
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/mcp", json={})

    assert response.status_code == HTTP_UNAUTHORIZED
    assert response.headers["www-authenticate"].startswith("Bearer")
