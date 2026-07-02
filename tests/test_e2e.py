# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Live Fusion E2E tests (optional)."""

from __future__ import annotations

import os

import pytest
from mcp.types import CallToolResult, TextContent

from community_vmware_desktop_hypervisor_mcp_server.handlers import invoke_power, vm_list_data
from community_vmware_desktop_hypervisor_mcp_server.schemas import PowerParams

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_vm_list_live() -> None:
    data = await vm_list_data()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_power_query_live() -> None:
    vmx = os.environ.get("VMCLI_E2E_VMX_PATH")
    if not vmx:
        pytest.skip("Set VMCLI_E2E_VMX_PATH to a .vmx file for power query e2e")
    result = await invoke_power(PowerParams(action="query", vmx_path=vmx))
    assert isinstance(result, CallToolResult)
    assert result.isError is not True
    item = result.content[0]
    assert isinstance(item, TextContent)
    assert len(item.text) > 0
