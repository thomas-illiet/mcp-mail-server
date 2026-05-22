from __future__ import annotations

import os
import secrets
from typing import TYPE_CHECKING

from fastmcp.server.auth import AccessToken, AuthProvider

from email_mcp.config.parsing import empty_to_none

if TYPE_CHECKING:
    from collections.abc import Mapping

MCP_BEARER_TOKEN_ENV = "MCP_BEARER_TOKEN"  # noqa: S105


class EnvBearerAuthProvider(AuthProvider):
    """FastMCP auth provider that validates one bearer token from the environment."""

    def __init__(self, expected_token: str) -> None:
        """Initialize the provider with the bearer token expected on MCP requests."""
        super().__init__()
        self._expected_token = expected_token

    async def verify_token(self, token: str) -> AccessToken | None:
        """Verify the presented bearer token and return FastMCP access metadata."""
        if not secrets.compare_digest(token, self._expected_token):
            return None

        return AccessToken(
            token=token,
            client_id="email-mcp-env-token",
            scopes=["email:mcp"],
            claims={"auth_type": "env_bearer"},
        )


def get_mcp_bearer_token(env: Mapping[str, str] | None = None) -> str | None:
    """Return the optional MCP bearer token from environment-style values."""
    source = os.environ if env is None else env
    return empty_to_none(source.get(MCP_BEARER_TOKEN_ENV))


def build_bearer_auth_provider(token: str | None) -> AuthProvider | None:
    """Build a FastMCP bearer auth provider when a token is configured."""
    if token is None:
        return None

    return EnvBearerAuthProvider(token)


def load_bearer_auth_provider(env: Mapping[str, str] | None = None) -> AuthProvider | None:
    """Load the optional FastMCP bearer auth provider from environment values."""
    return build_bearer_auth_provider(get_mcp_bearer_token(env))
