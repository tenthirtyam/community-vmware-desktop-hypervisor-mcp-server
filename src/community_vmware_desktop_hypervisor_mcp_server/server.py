# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""MCP server entry point for community-vmware-desktop-hypervisor-mcp-server."""

from __future__ import annotations

import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from .config import get_settings
from .context import AppContext, reset_app_context, set_app_context
from .platform_detector import resolve_vmcli
from .tools import register_tools
from .vmcli import VmCliRunner

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastMCP) -> AsyncIterator[None]:
    """Resolve vmcli once and share VmCliRunner across tool invocations."""
    binary = resolve_vmcli()
    token = set_app_context(AppContext(runner=VmCliRunner(binary)))
    logger.info("Using vmcli at %s", binary)
    try:
        yield
    finally:
        reset_app_context(token)


mcp = FastMCP("community-vmware-desktop-hypervisor-mcp-server", lifespan=lifespan)


def _configure_logging() -> None:
    """Configure package logging from environment-based settings."""
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.WARNING),
        stream=sys.stderr,
    )


def main() -> None:
    """Run the FastMCP server entry point."""
    _configure_logging()
    register_tools(mcp)
    mcp.run()


if __name__ == "__main__":
    main()
