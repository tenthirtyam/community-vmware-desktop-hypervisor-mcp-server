# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Tests for manifest loading."""

from __future__ import annotations

from community_vmware_desktop_hypervisor_mcp_server.manifest import (
    action_requires_vmx,
    get_commands,
    get_module_names,
    load_manifest,
    query_action_for_module,
)


def test_manifest_loads() -> None:
    manifest = load_manifest()
    assert manifest["version"] == "1.0"
    modules = manifest["modules"]
    assert "Power" in modules
    assert "Disk" in modules


def test_get_commands_power() -> None:
    commands = get_commands("Power")
    assert "Start" in commands
    assert "query" in commands
    assert len(commands) == 7


def test_module_names_count() -> None:
    names = get_module_names()
    assert len(names) >= 16


def test_manifest_command_counts() -> None:
    assert len(get_commands("Disk")) >= 30
    assert len(get_commands("Ethernet")) >= 15
    assert "Extend" in get_commands("Disk")
    assert "SetNetworkName" in get_commands("Ethernet")


def test_every_module_has_commands() -> None:
    for module in get_module_names():
        assert len(get_commands(module)) >= 1, f"{module} has no commands"


def test_query_action_for_module() -> None:
    assert query_action_for_module("Power") == "query"
    assert query_action_for_module("Serial") == "Query"
    assert query_action_for_module("Tools") == "Query"
    assert query_action_for_module("VMTemplate") is None


def test_action_requires_vmx() -> None:
    assert action_requires_vmx("VM", "Create") is False
    assert action_requires_vmx("VMTemplate", "Deploy") is False
    assert action_requires_vmx("Power", "Start") is True
