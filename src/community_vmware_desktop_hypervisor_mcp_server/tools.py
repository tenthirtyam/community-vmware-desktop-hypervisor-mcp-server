# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""MCP tool registrations for vmcli modules."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult

from .discovery import action_doc
from .handlers import (
    VmListEntry,
    discover_capabilities_data,
    invoke_guest,
    invoke_module,
    invoke_power,
    invoke_snapshot,
    invoke_vm_create,
    vm_list_data,
)
from .manifest import get_commands
from .schemas import (
    MODULE_PARAM_TYPES,
    MODULE_TOOL_NAMES,
    GuestParams,
    PowerParams,
    SnapshotParams,
    VmCreateParams,
    VmxValidatedParams,
)


@dataclass(frozen=True)
class GenericModuleToolSpec:
    """Registration metadata for one generic vmcli module tool."""

    module: str
    tool_name: str
    param_cls: type[VmxValidatedParams]


def _generic_module_tool_specs() -> tuple[GenericModuleToolSpec, ...]:
    """Return registration metadata for generic module-backed MCP tools."""
    return tuple(
        GenericModuleToolSpec(
            module=module,
            tool_name=MODULE_TOOL_NAMES[module],
            param_cls=param_cls,
        )
        for module, param_cls in MODULE_PARAM_TYPES.items()
    )


def _build_generic_module_tool(
    spec: GenericModuleToolSpec,
) -> Callable[..., Awaitable[CallToolResult]]:
    """Create a typed FastMCP handler for a generic vmcli module tool."""

    async def handler(params: VmxValidatedParams) -> CallToolResult:
        """Invoke the shared module handler with the generated parameter type."""
        return await invoke_module(spec.module, params)

    handler.__name__ = spec.tool_name
    handler.__annotations__ = {"params": spec.param_cls, "return": CallToolResult}
    handler.__doc__ = action_doc(spec.module, get_commands(spec.module))
    return handler


def _register_generic_module_tool(mcp: FastMCP, spec: GenericModuleToolSpec) -> None:
    """Register one generic module-backed tool on the FastMCP instance."""
    mcp.tool(name=spec.tool_name)(_build_generic_module_tool(spec))


def register_generated_module_tools(mcp: FastMCP) -> None:
    """Register MCP tools backed by the generic vmcli module handler."""
    for spec in _generic_module_tool_specs():
        _register_generic_module_tool(mcp, spec)


def register_core_tools(mcp: FastMCP) -> None:
    """Register explicit MCP tools with custom behavior or parameter models."""

    @mcp.tool()
    async def vm_list() -> list[VmListEntry]:
        """List virtual machines discovered on disk (.vmx inventory)."""
        return await vm_list_data()

    @mcp.tool()
    async def vm_discover_capabilities() -> dict[str, Any]:
        """Live-discover vmcli modules and commands from local --help output."""
        return await discover_capabilities_data()

    @mcp.tool()
    async def vm_power_management(params: PowerParams) -> CallToolResult:
        """Power module: query, Start, Stop, Pause, Reset, Suspend, Unpause."""
        return await invoke_power(params)

    vm_power_management.__doc__ = action_doc("Power", get_commands("Power"))

    @mcp.tool()
    async def vm_snapshot_management(params: SnapshotParams) -> CallToolResult:
        """Snapshot module: query, Take, Delete, Revert, Clone."""
        return await invoke_snapshot(params)

    vm_snapshot_management.__doc__ = action_doc("Snapshot", get_commands("Snapshot"))

    @mcp.tool()
    async def vm_guest_operations(params: GuestParams) -> CallToolResult:
        """Guest module: run, copyFrom, copyTo, ps, ls, mkdir, ..."""
        return await invoke_guest(params)

    vm_guest_operations.__doc__ = action_doc("Guest", get_commands("Guest"))

    @mcp.tool()
    async def vm_lifecycle(params: VmCreateParams) -> CallToolResult:
        """VM module: Create new virtual machine (-n, -d, -g/-c)."""
        return await invoke_vm_create(params)


def register_tools(mcp: FastMCP) -> None:
    """Register all MCP tools on the FastMCP instance."""
    register_core_tools(mcp)
    register_generated_module_tools(mcp)
