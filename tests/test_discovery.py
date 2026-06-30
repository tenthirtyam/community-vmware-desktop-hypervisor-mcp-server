# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Tests for vmcli help parsing."""

from __future__ import annotations

from pathlib import Path

from community_vmware_desktop_hypervisor_mcp_server.discovery import parse_module_commands

FIXTURES = Path(__file__).parent / "fixtures"


def test_disk_help_command_count() -> None:
    text = (FIXTURES / "disk_help.txt").read_text(encoding="utf-8")
    commands = parse_module_commands(text, "Disk")
    assert len(commands) >= 30
    assert "Extend" in commands
    assert "query" in commands
    assert "SetShares" in commands


def test_ethernet_help_command_count() -> None:
    text = (FIXTURES / "ethernet_help.txt").read_text(encoding="utf-8")
    commands = parse_module_commands(text, "Ethernet")
    assert len(commands) >= 15
    assert "SetNetworkName" in commands
    assert "query" in commands


def test_merge_usage_and_args() -> None:
    text = (FIXTURES / "disk_help.txt").read_text(encoding="utf-8")
    commands = parse_module_commands(text, "Disk")
    assert "Create" in commands
    assert commands == sorted(commands, key=str.lower)
