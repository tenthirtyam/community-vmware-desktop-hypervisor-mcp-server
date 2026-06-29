# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Pytest configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from community_vmware_desktop_hypervisor_mcp_server.context import (
    AppContext,
    reset_app_context,
    set_app_context,
)
from community_vmware_desktop_hypervisor_mcp_server.inventory import clear_inventory_cache
from community_vmware_desktop_hypervisor_mcp_server.platform_detector import resolve_vmcli
from community_vmware_desktop_hypervisor_mcp_server.vmcli import VmCliRunner


@pytest.fixture(autouse=True)
def _clear_inventory_cache() -> Generator[None, None, None]:
    """Reset the VM inventory cache around each test."""
    clear_inventory_cache()
    yield
    clear_inventory_cache()


@pytest.fixture(autouse=True)
def app_context(request: pytest.FixtureRequest) -> Generator[VmCliRunner, None, None]:
    """Mock runner for unit tests; real vmcli for @pytest.mark.e2e when Fusion is available."""
    if request.node.get_closest_marker("e2e"):
        try:
            binary = resolve_vmcli()
        except FileNotFoundError:
            pytest.skip("vmcli not installed; skipping e2e")
        runner = VmCliRunner(binary)
    else:
        runner = VmCliRunner(Path("/usr/bin/vmcli"))
        runner.run = AsyncMock()  # type: ignore[method-assign]
    token = set_app_context(AppContext(runner=runner))
    yield runner
    reset_app_context(token)
