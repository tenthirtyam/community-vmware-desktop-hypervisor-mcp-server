# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Manifest ↔ _generated_actions drift and command-count regression."""

from __future__ import annotations

import json
import typing
from pathlib import Path

import pytest

from community_vmware_desktop_hypervisor_mcp_server import (
    _generated_actions as gen,  # pyright: ignore[reportPrivateUsage]
)
from community_vmware_desktop_hypervisor_mcp_server.manifest import (
    get_action_literals,
    get_commands,
    get_module_names,
    is_valid_action,
    load_manifest,
)

FIXTURES = Path(__file__).parent / "fixtures"
COUNTS_PATH = FIXTURES / "manifest_command_counts.json"

MODULE_ACTION_TYPES: dict[str, object] = {
    "Chipset": gen.ChipsetAction,
    "ConfigParams": gen.ConfigParamsAction,
    "Disk": gen.DiskAction,
    "Ethernet": gen.EthernetAction,
    "Guest": gen.GuestAction,
    "HGFS": gen.HGFSAction,
    "MKS": gen.MKSAction,
    "Nvme": gen.NvmeAction,
    "Power": gen.PowerAction,
    "Sata": gen.SataAction,
    "Serial": gen.SerialAction,
    "Snapshot": gen.SnapshotAction,
    "Tools": gen.ToolsAction,
    "VM": gen.VMAction,
    "VMTemplate": gen.VMTemplateAction,
    "VProbes": gen.VProbesAction,
}


def test_all_modules_have_generated_literal() -> None:
    names = get_module_names()
    assert set(MODULE_ACTION_TYPES.keys()) == set(names)


@pytest.mark.parametrize("module", get_module_names())
def test_generated_literals_match_manifest(module: str) -> None:
    literal_type = MODULE_ACTION_TYPES[module]
    literal_actions = frozenset(typing.get_args(literal_type))
    manifest_actions = get_action_literals(module)
    assert literal_actions == manifest_actions, (
        f"{module}: manifest {sorted(manifest_actions)} != generated {sorted(literal_actions)}"
    )


def test_command_counts_match_snapshot() -> None:
    expected: dict[str, int] = json.loads(COUNTS_PATH.read_text(encoding="utf-8"))
    manifest = load_manifest()
    modules = manifest["modules"]
    for module, count in expected.items():
        actual = len(modules[module]["commands"])
        assert actual == count, f"{module}: expected {count} commands, got {actual}"


def test_is_valid_action() -> None:
    assert is_valid_action("Disk", "Extend")
    assert not is_valid_action("Disk", "NotReal")
    assert is_valid_action("Power", "query")
    assert get_commands("Power") == sorted(get_commands("Power"))
