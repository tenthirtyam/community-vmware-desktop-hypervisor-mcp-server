# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Load the checked-in vmcli capability manifest."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

MANIFEST_PATH = Path(__file__).parent / "manifest.json"


@lru_cache(maxsize=1)
def load_manifest() -> dict[str, Any]:
    """Load the checked-in capability manifest from disk once."""
    if not MANIFEST_PATH.is_file():
        msg = f"manifest not found: {MANIFEST_PATH}"
        raise FileNotFoundError(msg)
    data: dict[str, Any] = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return data


def get_module_names() -> list[str]:
    """Return manifest module names in sorted order."""
    manifest = load_manifest()
    modules = manifest.get("modules", {})
    return sorted(modules.keys())


def get_commands(module: str) -> list[str]:
    """Return sorted command names for a manifest module."""
    manifest = load_manifest()
    mod = manifest.get("modules", {}).get(module, {})
    commands = mod.get("commands", {})
    if isinstance(commands, dict):
        return sorted(commands.keys())
    return []


def get_action_literals(module: str) -> frozenset[str]:
    """Return the set of valid action names for a module from the manifest."""
    return frozenset(get_commands(module))


def is_valid_action(module: str, action: str) -> bool:
    """Return whether action is listed for module in manifest.json."""
    return action in get_action_literals(module)


VMX_OPTIONAL: dict[str, frozenset[str]] = {
    "VM": frozenset({"Create"}),
    "VMTemplate": frozenset({"Deploy"}),
}


def action_requires_vmx(module: str, action: str) -> bool:
    """Return whether a module action requires an existing VMX path."""
    return action not in VMX_OPTIONAL.get(module, frozenset())


def query_action_for_module(module: str) -> str | None:
    """Return the vmcli query subcommand name for module, if any."""
    for name in ("query", "Query"):
        if name in get_action_literals(module):
            return name
    return None
