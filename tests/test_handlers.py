# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Tests for handler orchestration and MCP error results."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from mcp.types import CallToolResult, TextContent

from community_vmware_desktop_hypervisor_mcp_server.handlers import (
    discover_capabilities_data,
    discover_capabilities_text,
    invoke_guest,
    invoke_module,
    invoke_power,
    invoke_snapshot,
    invoke_vm_create,
)

from community_vmware_desktop_hypervisor_mcp_server.schemas import (
    DiskParams,
    GuestParams,
    PowerParams,
    SnapshotParams,
    VmCreateParams,
)
from community_vmware_desktop_hypervisor_mcp_server.server_common import VmCliResult
from community_vmware_desktop_hypervisor_mcp_server.vmcli import VmCliRunner


def _text(result: CallToolResult) -> str:
    """Extract the first text payload from a CallToolResult."""
    item = result.content[0]
    assert isinstance(item, TextContent)
    return item.text


@pytest.mark.asyncio
async def test_invoke_power_success(app_context: VmCliRunner, tmp_path: Path) -> None:
    vmx = tmp_path / "test.vmx"
    vmx.write_text("# vmx\n", encoding="utf-8")
    ok = VmCliResult(ok=True, stdout='{"state":"on"}', stderr="", returncode=0, command=[])
    app_context.run.return_value = ok  # type: ignore[attr-defined]
    with patch(
        "community_vmware_desktop_hypervisor_mcp_server.handlers.resolve_vmx_path",
        return_value=vmx,
    ):
        result = await invoke_power(PowerParams(action="query", vmx_path=str(vmx)))
    assert _text(result) == '{"state":"on"}'
    assert result.isError is not True


@pytest.mark.asyncio
async def test_invoke_power_vmcli_error(app_context: VmCliRunner, tmp_path: Path) -> None:
    vmx = tmp_path / "test.vmx"
    vmx.write_text("# vmx\n", encoding="utf-8")
    fail = VmCliResult(
        ok=False,
        stdout="",
        stderr="VM is powered off",
        returncode=1,
        command=["Power", "query"],
    )
    app_context.run.return_value = fail  # type: ignore[attr-defined]
    with patch(
        "community_vmware_desktop_hypervisor_mcp_server.handlers.resolve_vmx_path",
        return_value=vmx,
    ):
        result = await invoke_power(PowerParams(action="query", vmx_path=str(vmx)))
    assert result.isError is True
    assert "powered off" in _text(result)


@pytest.mark.asyncio
async def test_invoke_power_start_paused_extra_args(
    app_context: VmCliRunner,
    tmp_path: Path,
) -> None:
    vmx = tmp_path / "test.vmx"
    vmx.write_text("# vmx\n", encoding="utf-8")
    ok = VmCliResult(ok=True, stdout="ok", stderr="", returncode=0, command=[])
    app_context.run.return_value = ok  # type: ignore[attr-defined]
    with patch(
        "community_vmware_desktop_hypervisor_mcp_server.handlers.resolve_vmx_path",
        return_value=vmx,
    ):
        await invoke_power(
            PowerParams(action="Start", vmx_path=str(vmx), paused=True),
        )
    argv = app_context.run.await_args.args[0]  # type: ignore[attr-defined]
    assert "--paused" in argv


@pytest.mark.asyncio
async def test_invoke_disk_builds_argv(app_context: VmCliRunner, tmp_path: Path) -> None:
    ok = VmCliResult(ok=True, stdout="ok", stderr="", returncode=0, command=[])
    app_context.run.return_value = ok  # type: ignore[attr-defined]
    vmx = tmp_path / "test.vmx"
    with patch(
        "community_vmware_desktop_hypervisor_mcp_server.handlers.resolve_vmx_path",
        return_value=vmx,
    ):
        await invoke_module("Disk", DiskParams(action="query", vmx_path=str(vmx)))
    argv = app_context.run.await_args.args[0]  # type: ignore[attr-defined]
    assert argv[0] == str(vmx)
    assert "Disk" in argv
    assert "query" in argv


@pytest.mark.asyncio
async def test_invoke_snapshot_take_extra_args(app_context: VmCliRunner, tmp_path: Path) -> None:
    vmx = tmp_path / "test.vmx"
    vmx.write_text("# vmx\n", encoding="utf-8")
    ok = VmCliResult(ok=True, stdout="ok", stderr="", returncode=0, command=[])
    app_context.run.return_value = ok  # type: ignore[attr-defined]
    with patch(
        "community_vmware_desktop_hypervisor_mcp_server.handlers.resolve_vmx_path",
        return_value=vmx,
    ):
        await invoke_snapshot(
            SnapshotParams(
                action="Take",
                vmx_path=str(vmx),
                snapshot_name="snap1",
                include_memory=True,
            ),
        )
    argv = app_context.run.await_args.args[0]  # type: ignore[attr-defined]
    assert "--memory" in argv
    assert "snap1" in argv


@pytest.mark.asyncio
async def test_invoke_guest_run_builds_argv(app_context: VmCliRunner, tmp_path: Path) -> None:
    vmx = tmp_path / "test.vmx"
    vmx.write_text("# vmx\n", encoding="utf-8")
    ok = VmCliResult(ok=True, stdout="31180", stderr="", returncode=0, command=[])
    app_context.run.return_value = ok  # type: ignore[attr-defined]
    with patch(
        "community_vmware_desktop_hypervisor_mcp_server.handlers.resolve_vmx_path",
        return_value=vmx,
    ):
        result = await invoke_guest(
            GuestParams(
                action="run",
                vmx_path=str(vmx),
                username="user",
                password="pass",
                program="/bin/sh",
                program_args=["-c", "uname -a > /tmp/uname.txt"],
            )
        )
    assert result.isError is not True
    argv = app_context.run.await_args.args[0]  # type: ignore[attr-defined]
    assert "Guest" in argv
    assert "run" in argv
    assert "-u" in argv
    assert "user" in argv
    assert "-p" in argv
    assert "pass" in argv
    assert "/bin/sh" in argv
    assert "-c" in argv
    assert "uname -a > /tmp/uname.txt" in argv


@pytest.mark.asyncio
async def test_invoke_vm_create(app_context: VmCliRunner) -> None:
    ok = VmCliResult(ok=True, stdout="created", stderr="", returncode=0, command=[])
    app_context.run.return_value = ok  # type: ignore[attr-defined]
    result = await invoke_vm_create(VmCreateParams(name="vm1", dirpath="/tmp/vms"))
    assert _text(result) == "created"
    argv = app_context.run.await_args.args[0]  # type: ignore[attr-defined]
    assert argv == ["VM", "Create", "-n", "vm1", "-d", "/tmp/vms"]


@pytest.mark.asyncio
async def test_discover_capabilities_text() -> None:
    fake_manifest = {"version": "1.0", "modules": {}}
    with (
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.handlers.discover",
            new=AsyncMock(return_value=fake_manifest),
        ),
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.handlers.get_runner",
        ) as mock_get_runner,
    ):
        mock_get_runner.return_value.binary = Path("/usr/bin/vmcli")
        text = await discover_capabilities_text()
    assert "1.0" in text


@pytest.mark.asyncio
async def test_discover_capabilities_data_uses_runner_binary() -> None:
    fake_manifest = {"version": "1.0", "modules": {}}
    with (
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.handlers.discover",
            new=AsyncMock(return_value=fake_manifest),
        ) as mock_discover,
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.handlers.get_runner",
        ) as mock_get_runner,
    ):
        mock_get_runner.return_value.binary = Path("/usr/bin/vmcli")
        data = await discover_capabilities_data()

    assert data == fake_manifest
    mock_discover.assert_awaited_once_with(Path("/usr/bin/vmcli"))
