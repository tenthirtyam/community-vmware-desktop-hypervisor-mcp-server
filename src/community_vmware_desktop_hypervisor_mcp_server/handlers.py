# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Shared handler logic for module-grouped MCP tools."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypedDict, cast

from mcp.types import CallToolResult

from .context import get_runner
from .discovery import discover
from .inventory import discover_vms, resolve_vmx_path
from .schemas import (
    GuestParams,
    ModuleInvokeParams,
    PowerParams,
    SnapshotParams,
    VmCreateParams,
    build_guest_extra_args,
    build_power_extra_args,
    build_snapshot_extra_args,
    build_vm_create_args,
)
from .server_common import tool_result_from_vmcli
from .vmcli import run_module_command

ExtraArgsFn = Callable[[ModuleInvokeParams], list[str]]


class VmListEntry(TypedDict):
    id: str
    display_name: str
    vmx_path: str


async def invoke_module(
    module: str,
    params: ModuleInvokeParams,
    *,
    extra_args: ExtraArgsFn | None = None,
) -> CallToolResult:
    """Resolve inputs, run a vmcli module command, and map the MCP result."""
    vmx: Path | None = None
    if params.vmx_path:
        vmx = resolve_vmx_path(params.vmx_path)

    command_args = extra_args(params) if extra_args else list(params.command_args)

    result = await run_module_command(
        module,
        str(params.action),
        vmx_path=vmx,
        command_args=command_args,
        vmx_position=params.vmx_position,
        verbose=params.verbose,
        output_format=params.output_format,
    )
    return tool_result_from_vmcli(result)


async def invoke_power(params: PowerParams) -> CallToolResult:
    """Invoke the Power module with derived convenience flags."""
    return await invoke_module(
        "Power",
        params,
        extra_args=cast("ExtraArgsFn", cast("object", build_power_extra_args)),
    )


async def invoke_snapshot(params: SnapshotParams) -> CallToolResult:
    """Invoke the Snapshot module with derived convenience flags."""
    return await invoke_module(
        "Snapshot",
        params,
        extra_args=cast("ExtraArgsFn", cast("object", build_snapshot_extra_args)),
    )


async def invoke_guest(params: GuestParams) -> CallToolResult:
    """Invoke the Guest module, using typed fields for the run action."""
    return await invoke_module(
        "Guest",
        params,
        extra_args=cast("ExtraArgsFn", cast("object", build_guest_extra_args)),
    )


async def invoke_vm_create(params: VmCreateParams) -> CallToolResult:
    """Invoke VM Create with the dedicated typed parameter model."""
    command_args = build_vm_create_args(params)
    result = await run_module_command(
        "VM",
        "Create",
        command_args=command_args,
        verbose=params.verbose,
    )
    return tool_result_from_vmcli(result)


async def vm_list_data() -> list[VmListEntry]:
    """Return the refreshed VM inventory as structured data."""
    entries = discover_vms(refresh=True)
    return [
        {
            "id": e.id,
            "display_name": e.display_name,
            "vmx_path": e.vmx_path,
        }
        for e in entries
    ]


async def vm_list_text() -> str:
    """Return the refreshed VM inventory as pretty-printed JSON text."""
    return json.dumps(await vm_list_data(), indent=2)


async def discover_capabilities_data() -> dict[str, Any]:
    """Return live vmcli capability discovery using the shared runner binary."""
    return await discover(get_runner().binary)


async def discover_capabilities_text() -> str:
    """Return live vmcli capability discovery as pretty-printed JSON text."""
    return json.dumps(await discover_capabilities_data(), indent=2)
