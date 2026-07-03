# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Live Fusion E2E: exercise MCP handlers against a real .vmx."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
from mcp.types import CallToolResult, TextContent

from community_vmware_desktop_hypervisor_mcp_server.handlers import (
    invoke_module,
    invoke_power,
    vm_list_data,
)
from community_vmware_desktop_hypervisor_mcp_server.manifest import query_action_for_module
from community_vmware_desktop_hypervisor_mcp_server.schemas import (
    MODULE_PARAM_TYPES,
    PowerParams,
    ToolsParams,
)

# Import suite runner from scripts (repo root on path via conftest PYTHONPATH in CI)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.e2e_mcp_capabilities import run_suite

pytestmark = pytest.mark.e2e

VMX = os.environ.get("VMCLI_E2E_VMX_PATH")


@pytest.fixture
def e2e_vmx() -> str:
    """Return the configured VMX path for live end-to-end tests."""
    if not VMX:
        pytest.skip("Set VMCLI_E2E_VMX_PATH to a .vmx file for e2e")
    return VMX


@pytest.mark.asyncio
async def test_vm_list_finds_vmx(e2e_vmx: str) -> None:
    data = await vm_list_data()
    paths = [row["vmx_path"] for row in data]
    assert e2e_vmx in paths or any(e2e_vmx in p for p in paths)


@pytest.mark.asyncio
async def test_power_query_json(e2e_vmx: str) -> None:
    result = await invoke_power(PowerParams(action="query", vmx_path=e2e_vmx))
    assert isinstance(result, CallToolResult)
    assert result.isError is not True
    item = result.content[0]
    assert isinstance(item, TextContent)
    payload = json.loads(item.text)
    assert "PowerState" in payload


@pytest.mark.asyncio
async def test_power_stop_default_op_type(e2e_vmx: str) -> None:
    query = await invoke_power(PowerParams(action="query", vmx_path=e2e_vmx))
    q_item = query.content[0]
    assert isinstance(q_item, TextContent)
    state = json.loads(q_item.text).get("PowerState", "").lower()
    if state != "on":
        pytest.skip("VM is not powered on; cannot test Stop")

    tools = await invoke_module(ToolsParams(action="Query", vmx_path=e2e_vmx))
    t_item = tools.content[0]
    if isinstance(t_item, TextContent):
        tools_state = json.loads(t_item.text).get("runningStatus", "").lower()
        if tools_state != "running":
            pytest.skip("VMware Tools not running; trySoft Stop requires Tools")

    result = await invoke_power(PowerParams(action="Stop", vmx_path=e2e_vmx))
    assert result.isError is not True


@pytest.mark.parametrize("module", sorted(MODULE_PARAM_TYPES))
def test_module_has_query_action_or_skip(module: str) -> None:
    action = query_action_for_module(module)
    if module == "VMTemplate":
        assert action is None
    else:
        assert action in ("query", "Query")


@pytest.mark.asyncio
async def test_full_mcp_capability_suite(e2e_vmx: str) -> None:
    results = await run_suite(e2e_vmx, exercise_guest=False)
    failed = [r for r in results if not r.ok and not r.skipped]
    assert not failed, "\n".join(f"{r.name}: {r.detail}" for r in failed)
