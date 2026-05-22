from __future__ import annotations

import logging


def configure_python_logging(log_level: str) -> None:
    """Configure standard Python logs for the MCP server process."""
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
