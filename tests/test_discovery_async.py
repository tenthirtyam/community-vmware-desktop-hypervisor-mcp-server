# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Tests for async discovery.discover() with mocked vmcli help."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from community_vmware_desktop_hypervisor_mcp_server.discovery import (
    action_doc,
    discover,
    parse_module_commands,
    parse_top_level,
    render_generated_actions,
    run_help,
)

FIXTURES = Path(__file__).parent / "fixtures"
ROOT_HELP = """Usage: vmcli [<vmx location>] <Module> [GLOBAL OPTIONS] <Command> [OPTIONS]

Available modules:
\tDisk
\t\tModule to perform disk operations.
\tEthernet
\t\tSetup the ethernet configuration in the guest.
\tPower
\t\tSet the power state of the vm.
"""


@pytest.mark.asyncio
async def test_discover_builds_modules() -> None:
    disk_help = (FIXTURES / "disk_help.txt").read_text(encoding="utf-8")
    ethernet_help = (FIXTURES / "ethernet_help.txt").read_text(encoding="utf-8")
    power_help = 'Arguments available to module "Power":\n\tquery\n\tStart\n\tStop\n'

    async def fake_run_help(_vmcli: Path, args: list[str]) -> str:
        """Return fixture-backed help text for mocked discovery calls."""
        if args == ["--help"]:
            return ROOT_HELP
        if args == ["Disk", "--help"]:
            return disk_help
        if args == ["Ethernet", "--help"]:
            return ethernet_help
        if args == ["Power", "--help"]:
            return power_help
        return ""

    with patch(
        "community_vmware_desktop_hypervisor_mcp_server.discovery.run_help",
        new=AsyncMock(side_effect=fake_run_help),
    ):
        manifest = await discover(Path("/usr/bin/vmcli"))

    assert manifest["version"] == "1.0"
    assert "Disk" in manifest["modules"]
    assert len(manifest["modules"]["Disk"]["commands"]) >= 30
    assert "Extend" in manifest["modules"]["Disk"]["commands"]
    assert len(manifest["modules"]["Ethernet"]["commands"]) >= 15
    assert "query" in manifest["modules"]["Power"]["commands"]


def test_parse_module_commands_sorted() -> None:
    text = (FIXTURES / "disk_help.txt").read_text(encoding="utf-8")
    commands = parse_module_commands(text, "Disk")
    assert commands == sorted(commands, key=str.lower)


def test_parse_top_level() -> None:
    modules = parse_top_level(ROOT_HELP)
    assert modules["Disk"] == "Module to perform disk operations."
    assert modules["Power"] == "Set the power state of the vm."


def test_render_generated_actions() -> None:
    modules = {
        "Power": {"commands": {"query": {}, "Start": {}}},
        "Empty": {"commands": {}},
    }
    text = render_generated_actions(modules)
    assert "PowerAction = Literal" in text
    assert "query" in text
    assert "EmptyAction" not in text


def test_action_doc_truncates() -> None:
    doc = action_doc("Disk", [f"cmd{i}" for i in range(20)])
    assert "..." in doc
    assert "Valid actions:" in doc


@pytest.mark.asyncio
async def test_run_help_subprocess() -> None:
    proc = AsyncMock()
    proc.communicate = AsyncMock(return_value=(b"help text\n", b""))
    proc.returncode = 0
    with patch(
        "community_vmware_desktop_hypervisor_mcp_server.discovery.asyncio.create_subprocess_exec",
        new=AsyncMock(return_value=proc),
    ):
        text = await run_help(Path("/usr/bin/vmcli"), ["--help"])
    assert text == "help text\n"


@pytest.mark.asyncio
async def test_run_help_failure_raises() -> None:
    proc = AsyncMock()
    proc.communicate = AsyncMock(return_value=(b"", b""))
    proc.returncode = 1
    with (
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.discovery.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ),
        pytest.raises(RuntimeError, match="failed"),
    ):
        await run_help(Path("/usr/bin/vmcli"), ["BadModule", "--help"])
