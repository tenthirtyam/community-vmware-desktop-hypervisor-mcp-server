# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Tests for vmcli argv building and error handling."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import community_vmware_desktop_hypervisor_mcp_server.context as context_module
from community_vmware_desktop_hypervisor_mcp_server.context import (
    get_app_context,
    reset_app_context,
)
from community_vmware_desktop_hypervisor_mcp_server.manifest import action_requires_vmx
from community_vmware_desktop_hypervisor_mcp_server.server_common import VmCliResult
from community_vmware_desktop_hypervisor_mcp_server.vmcli import (
    CommandBuilder,
    VmCliRunner,
    _query_format_args,  # pyright: ignore[reportPrivateUsage]
)


def test_command_builder_vmx_first(tmp_path: Path) -> None:
    vmx = tmp_path / "test.vmx"
    argv = CommandBuilder(
        "Power",
        "Start",
        vmx_path=vmx,
        command_args=["--soft"],
        verbose=True,
    ).build()
    assert argv == [str(vmx), "Power", "Start", "--verbose", "--soft"]


def test_command_builder_vmx_last(tmp_path: Path) -> None:
    vmx = tmp_path / "test.vmx"
    argv = CommandBuilder(
        "Power",
        "query",
        vmx_path=vmx,
        vmx_position="last",
        extra_format_args=["-f", "json"],
    ).build()
    assert argv == ["Power", "query", "-f", "json", str(vmx)]


def test_query_format_override() -> None:
    assert _query_format_args("query", "yaml") == ["-f", "yaml"]


def test_vmcli_result_error_text() -> None:
    result = VmCliResult(
        ok=False,
        stdout="",
        stderr="VM is powered off",
        returncode=1,
        command=["Power", "query"],
    )
    assert "VMware vmcli error" in result.text
    assert "powered off" in result.text


def test_action_requires_vmx_from_manifest() -> None:
    assert action_requires_vmx("VM", "Create") is False
    assert action_requires_vmx("Power", "Start") is True


@pytest.mark.asyncio
async def test_runner_timeout_message() -> None:
    runner = VmCliRunner(Path("/usr/bin/false"))
    proc = MagicMock()
    proc.communicate = MagicMock()
    proc.kill = MagicMock()
    proc.wait = AsyncMock()
    with patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=proc)):
        with patch("asyncio.wait_for", new=AsyncMock(side_effect=TimeoutError)):
            result = await runner.run(["Power", "query"])
    assert result.ok is False
    assert "timed out" in result.stderr


def test_get_app_context_creates_default_runner() -> None:
    token = context_module._app_context.set(None)
    try:
        ctx = get_app_context()
    finally:
        reset_app_context(token)

    assert isinstance(ctx.runner, VmCliRunner)
