# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Discover .vmx files and resolve vmx_path aliases."""

from __future__ import annotations

import hashlib
import os
import platform
from dataclasses import dataclass
from pathlib import Path

from .config import get_settings

_inventory_cache: list[VmEntry] | None = None


@dataclass(frozen=True)
class VmEntry:
    """A discovered virtual machine on disk."""

    id: str
    display_name: str
    vmx_path: str


def _default_search_paths() -> list[Path]:
    """Return the ordered set of directories to scan for VMX files."""
    paths: list[Path] = []
    settings = get_settings()
    for raw in settings.vm_search_paths:
        paths.append(Path(raw).expanduser())
    home = Path.home()
    system = platform.system().casefold()
    if system == "darwin":
        paths.extend(
            [
                Path("/Applications/Virtual Machines"),
                home / "Virtual Machines.localized",
                home / "Documents/Virtual Machines.localized",
            ]
        )
    elif system == "windows":
        paths.extend(
            [
                home / "Documents/Virtual Machines",
                Path(os.environ.get("USERPROFILE", str(home))) / "Virtual Machines",
            ]
        )
    else:
        paths.append(home / "vmware")
        paths.append(home / "Virtual Machines")
    seen: set[Path] = set()
    unique: list[Path] = []
    for p in paths:
        resolved = p.expanduser()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(resolved)
    return unique


def _vmx_id(vmx: Path) -> str:
    """Return a stable short identifier for a VMX path."""
    digest = hashlib.sha256(str(vmx.resolve()).encode()).hexdigest()
    return digest[:12]


def discover_vms(*, refresh: bool = False) -> list[VmEntry]:
    """Discover VMX files on disk and cache the resulting inventory."""
    global _inventory_cache
    if _inventory_cache is not None and not refresh:
        return list(_inventory_cache)

    entries: list[VmEntry] = []
    seen_paths: set[Path] = set()
    for root in _default_search_paths():
        if not root.is_dir():
            continue
        for vmx in root.rglob("*.vmx"):
            if not vmx.is_file():
                continue
            resolved = vmx.resolve()
            if resolved in seen_paths:
                continue
            seen_paths.add(resolved)
            display = vmx.stem
            entries.append(
                VmEntry(
                    id=_vmx_id(vmx),
                    display_name=display,
                    vmx_path=str(resolved),
                )
            )
    entries.sort(key=lambda e: e.display_name.lower())
    _inventory_cache = entries
    return list(entries)


def resolve_vmx_path(vmx_path: str) -> Path:
    """Resolve absolute .vmx path, or inventory id / display_name."""
    candidate = Path(vmx_path).expanduser()
    if candidate.is_file():
        if candidate.suffix.lower() != ".vmx":
            msg = f"vmx_path must end with .vmx: {vmx_path}"
            raise ValueError(msg)
        return candidate.resolve()

    needle = vmx_path.strip().lower()
    for entry in discover_vms():
        if entry.id == vmx_path or entry.id.lower() == needle:
            return Path(entry.vmx_path)
        if entry.display_name.lower() == needle:
            return Path(entry.vmx_path)
        if Path(entry.vmx_path).name.lower() == needle:
            return Path(entry.vmx_path)

    msg = (
        f"Could not resolve vmx_path '{vmx_path}'. "
        "Use an absolute .vmx path or run vm_list for id/display_name."
    )
    raise FileNotFoundError(msg)


def clear_inventory_cache() -> None:
    """Clear the cached VM inventory."""
    global _inventory_cache
    _inventory_cache = None
