# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Run full MCP capability smoke tests against a live .vmx (Fusion/Workstation)."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

from mcp.types import CallToolResult, TextContent

from community_vmware_desktop_hypervisor_mcp_server.context import (
    AppContext,
    reset_app_context,
    set_app_context,
)
from community_vmware_desktop_hypervisor_mcp_server.handlers import (
    discover_capabilities_text,
    invoke_module,
    invoke_power,
    vm_list_text,
)
from community_vmware_desktop_hypervisor_mcp_server.inventory import clear_inventory_cache
from community_vmware_desktop_hypervisor_mcp_server.manifest import query_action_for_module
from community_vmware_desktop_hypervisor_mcp_server.platform_detector import resolve_vmcli
from community_vmware_desktop_hypervisor_mcp_server.schemas import (
    MODULE_PARAM_TYPES,
    MODULE_TOOL_NAMES,
    PowerParams,
    SnapshotParams,
)
from community_vmware_desktop_hypervisor_mcp_server.vmcli import VmCliRunner

if TYPE_CHECKING:
    from collections.abc import Awaitable


@dataclass
class CaseResult:
    name: str
    ok: bool
    detail: str
    skipped: bool = False


RecordPayload = CallToolResult | CaseResult | str


def _write_stdout(text: str) -> None:
    """Write a single line to stdout."""
    sys.stdout.write(f"{text}\n")


def _write_stderr(text: str) -> None:
    """Write a single line to stderr."""
    sys.stderr.write(f"{text}\n")


def _get_e2e_vmx_path() -> str | None:
    """Return the configured VMX path for live end-to-end runs, if any."""
    return os.environ.get("VMCLI_E2E_VMX_PATH")


def _raise_unexpected_result_type(result: object) -> None:
    """Raise a clear error for unsupported helper return types."""
    msg = f"Unexpected result type: {type(result).__name__}"
    raise TypeError(msg)


def _first_text(result: CallToolResult, fallback: str = "") -> str:
    """Return the text of the first TextContent item, or *fallback*."""
    if not result.content:
        return fallback
    item = result.content[0]
    return item.text if isinstance(item, TextContent) else fallback


def _result_ok(result: CallToolResult) -> tuple[bool, str]:
    """Convert a tool result into a compact success flag and detail string."""
    if result.isError:
        text = _first_text(result, "unknown error")
        return False, text[:500]
    text = _first_text(result)
    return True, text[:200] if text else "(empty)"


async def _power_state(vmx: str) -> str | None:
    """Return the VM power state from a query result, if readable."""
    result = await invoke_power(PowerParams(action="query", vmx_path=vmx))
    if result.isError:
        return None
    text = _first_text(result)
    try:
        data = json.loads(text)
        return str(data.get("PowerState", "")).lower()
    except json.JSONDecodeError:
        return None


async def _run_query_module(module: str, vmx: str) -> CaseResult:
    """Run one module's query action and normalize its outcome."""
    action = query_action_for_module(module)
    tool = MODULE_TOOL_NAMES[module]
    if action is None:
        return CaseResult(tool, True, "no query action (skipped)", skipped=True)

    if module == "Guest":
        state = await _power_state(vmx)
        if state != "on":
            return CaseResult(
                tool,
                True,
                "VM offline; guest query requires powered-on VM (skipped)",
                skipped=True,
            )

    param_cls = MODULE_PARAM_TYPES[module]
    params = param_cls(action=action, vmx_path=vmx)  # type: ignore[arg-type]
    result = await invoke_module(module, params)
    ok, detail = _result_ok(result)
    return CaseResult(f"{tool}.{action}", ok, detail)


async def run_suite(vmx: str, *, exercise_guest: bool) -> list[CaseResult]:
    """Run the live MCP capability smoke-test suite for one VMX path."""
    clear_inventory_cache()
    results: list[CaseResult] = []

    async def record(name: str, coro: Awaitable[RecordPayload]) -> None:
        """Await one action and append a normalized result entry."""
        ok: bool = False
        detail: str = ""
        skipped: bool = False
        try:
            out = await coro
            if isinstance(out, CallToolResult):
                ok, detail = _result_ok(out)
            elif isinstance(out, CaseResult):
                results.append(out)
                return
            elif isinstance(out, str):
                ok, detail = True, out[:200]
            else:
                _raise_unexpected_result_type(out)
        except Exception as exc:
            ok, detail, skipped = False, f"{type(exc).__name__}: {exc}", False
        results.append(CaseResult(name, ok, detail, skipped=skipped))

    await record("vm_list", vm_list_text())
    await record("vm_discover_capabilities", discover_capabilities_text())

    await record(
        "vm_power_management.query",
        invoke_power(PowerParams(action="query", vmx_path=vmx)),
    )
    await record(
        "vm_snapshot_management.query",
        invoke_module("Snapshot", SnapshotParams(action="query", vmx_path=vmx)),
    )

    for module in sorted(MODULE_PARAM_TYPES):
        await record(MODULE_TOOL_NAMES[module], _run_query_module(module, vmx))

    guest_action = query_action_for_module("Guest")
    if exercise_guest and guest_action:
        state = await _power_state(vmx)
        if state != "on":
            await record(
                "vm_power_management.Start",
                invoke_power(PowerParams(action="Start", vmx_path=vmx, soft=True)),
            )
            await asyncio.sleep(5)
        await record(
            f"vm_guest_operations.{guest_action}",
            invoke_module(
                "Guest",
                MODULE_PARAM_TYPES["Guest"](action=guest_action, vmx_path=vmx),  # type: ignore[arg-type]
            ),
        )
    if await _power_state(vmx) == "on":
        await record(
            "vm_power_management.Stop",
            invoke_power(PowerParams(action="Stop", vmx_path=vmx)),
        )
    else:
        results.append(
            CaseResult(
                "vm_power_management.Stop",
                True,
                "VM already off (skipped)",
                skipped=True,
            )
        )

    await record(
        "vm_chipset_operations.SetVCpuCount",
        invoke_module(
            "Chipset",
            MODULE_PARAM_TYPES["Chipset"](
                action="SetVCpuCount",
                vmx_path=vmx,
                command_args=["4"],
            ),
        ),
    )

    return results


def main() -> int:
    """Run the e2e capability suite from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--vmx",
        default=_get_e2e_vmx_path(),
        help="Path to .vmx (or VMCLI_E2E_VMX_PATH env var)",
    )
    parser.add_argument(
        "--exercise-guest",
        action="store_true",
        help="Power on VM if needed and run Guest query",
    )
    args = parser.parse_args()
    if not args.vmx:
        _write_stderr("Set --vmx or VMCLI_E2E_VMX_PATH")
        return 2

    binary = resolve_vmcli()
    token = set_app_context(AppContext(runner=VmCliRunner(binary)))
    try:
        results = asyncio.run(run_suite(args.vmx, exercise_guest=args.exercise_guest))
    finally:
        reset_app_context(token)

    failed = [r for r in results if not r.ok and not r.skipped]
    skipped = [r for r in results if r.skipped]
    for r in results:
        status = "SKIP" if r.skipped else "PASS" if r.ok else "FAIL"
        _write_stdout(f"{status}\t{r.name}\t{r.detail}")

    _write_stdout(
        json.dumps(
            {
                "passed": len([r for r in results if r.ok and not r.skipped]),
                "skipped": len(skipped),
                "failed": len(failed),
            },
            indent=2,
        ),
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
