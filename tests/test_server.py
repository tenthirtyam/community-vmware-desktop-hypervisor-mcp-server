# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Tests for server lifespan and tool registration."""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import patch

import pytest
from mcp.server.fastmcp import FastMCP

from community_vmware_desktop_hypervisor_mcp_server.context import get_app_context
from community_vmware_desktop_hypervisor_mcp_server.server import (  # pyright: ignore[reportPrivateUsage]
    _configure_logging,
    lifespan,
    main,
)
from community_vmware_desktop_hypervisor_mcp_server.tools import register_tools


@pytest.mark.asyncio
async def test_lifespan_sets_runner() -> None:
    fake_binary = Path("/usr/bin/vmcli")
    with patch(
        "community_vmware_desktop_hypervisor_mcp_server.server.resolve_vmcli",
        return_value=fake_binary,
    ):
        async with lifespan(FastMCP("test")):
            ctx = get_app_context()
            assert ctx.runner.binary == fake_binary


def test_register_tools_smoke() -> None:
    mcp = FastMCP("test")
    register_tools(mcp)
    tools = mcp._tool_manager.list_tools()
    names = {t.name for t in tools}
    assert "vm_list" in names
    assert "vm_disk_operations" in names
    assert "vm_power_management" in names
    assert len(names) >= 18


def test_configure_logging_uses_settings() -> None:
    with (
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.server.get_settings",
        ) as mock_get_settings,
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.server.logging.basicConfig"
        ) as mock_basic_config,
    ):
        mock_get_settings.return_value.log_level = "INFO"
        _configure_logging()

    mock_basic_config.assert_called_once_with(level=logging.INFO, stream=__import__("sys").stderr)


def test_main_registers_tools_and_runs_server() -> None:
    with (
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.server._configure_logging"
        ) as mock_logging,
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.server.register_tools"
        ) as mock_register_tools,
        patch("community_vmware_desktop_hypervisor_mcp_server.server.mcp.run") as mock_run,
    ):
        main()

    mock_logging.assert_called_once_with()
    mock_register_tools.assert_called_once()
    mock_run.assert_called_once_with()
