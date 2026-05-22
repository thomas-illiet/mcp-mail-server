from __future__ import annotations

from typing import Any, Protocol


class ToolContext(Protocol):
    """Subset of FastMCP Context used by the email sending workflow."""

    async def report_progress(
        self,
        progress: float,
        total: float | None = None,
        message: str | None = None,
    ) -> None:
        """Report tool progress to clients that supplied a progress token."""
        ...

    async def debug(
        self,
        message: str,
        logger_name: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Send a debug log event to the MCP client."""
        ...

    async def info(
        self,
        message: str,
        logger_name: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Send an informational log event to the MCP client."""
        ...

    async def warning(
        self,
        message: str,
        logger_name: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Send a warning log event to the MCP client."""
        ...

    async def error(
        self,
        message: str,
        logger_name: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Send an error log event to the MCP client."""
        ...
