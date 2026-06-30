# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Tests for VM inventory and vmx_path resolution."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from community_vmware_desktop_hypervisor_mcp_server.inventory import (
    VmEntry,
    clear_inventory_cache,
    discover_vms,
    resolve_vmx_path,
)


def test_resolve_absolute_vmx(tmp_path: Path) -> None:
    vmx = tmp_path / "guest.vmx"
    vmx.write_text("# vmx\n", encoding="utf-8")
    resolved = resolve_vmx_path(str(vmx))
    assert resolved == vmx.resolve()


def test_resolve_by_inventory_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    vmx = tmp_path / "my-guest.vmx"
    vmx.write_text("# vmx\n", encoding="utf-8")

    def fake_discover(*, refresh: bool = False) -> list[VmEntry]:  # noqa: ARG001
        """Return a single fake inventory entry for alias resolution tests."""
        return [
            VmEntry(
                id="abc123",
                display_name="my-guest",
                vmx_path=str(vmx.resolve()),
            )
        ]

    monkeypatch.setattr(
        "community_vmware_desktop_hypervisor_mcp_server.inventory.discover_vms",
        fake_discover,
    )
    assert resolve_vmx_path("abc123") == vmx.resolve()
    assert resolve_vmx_path("my-guest") == vmx.resolve()


def test_resolve_missing_raises() -> None:
    with pytest.raises(FileNotFoundError, match="Could not resolve"):
        resolve_vmx_path("nonexistent-vm-xyz")


def test_default_search_paths_darwin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "community_vmware_desktop_hypervisor_mcp_server.inventory.platform.system",
        lambda: "Darwin",
    )
    from community_vmware_desktop_hypervisor_mcp_server.inventory import _default_search_paths

    paths = _default_search_paths()
    assert Path("/Applications/Virtual Machines") in paths


def test_default_search_paths_windows_and_custom(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    home = tmp_path / "home"
    profile = tmp_path / "profile"
    monkeypatch.setattr(
        "community_vmware_desktop_hypervisor_mcp_server.inventory.get_settings",
        lambda: SimpleNamespace(vm_search_paths=(str(tmp_path / "custom"),)),
    )
    monkeypatch.setattr(
        "community_vmware_desktop_hypervisor_mcp_server.inventory.platform.system",
        lambda: "Windows",
    )
    monkeypatch.setattr(
        "community_vmware_desktop_hypervisor_mcp_server.inventory.Path.home",
        lambda: home,
    )
    monkeypatch.setenv("USERPROFILE", str(profile))
    from community_vmware_desktop_hypervisor_mcp_server.inventory import _default_search_paths

    paths = _default_search_paths()
    assert tmp_path / "custom" in paths
    assert home / "Documents/Virtual Machines" in paths
    assert profile / "Virtual Machines" in paths


def test_default_search_paths_other_platform_deduplicates(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    home = tmp_path / "home"
    custom = home / "vmware"
    monkeypatch.setattr(
        "community_vmware_desktop_hypervisor_mcp_server.inventory.get_settings",
        lambda: SimpleNamespace(vm_search_paths=(str(custom), str(custom))),
    )
    monkeypatch.setattr(
        "community_vmware_desktop_hypervisor_mcp_server.inventory.platform.system",
        lambda: "Linux",
    )
    monkeypatch.setattr(
        "community_vmware_desktop_hypervisor_mcp_server.inventory.Path.home",
        lambda: home,
    )
    from community_vmware_desktop_hypervisor_mcp_server.inventory import _default_search_paths

    paths = _default_search_paths()
    assert paths.count(custom) == 1
    assert home / "Virtual Machines" in paths


def test_discover_vms_finds_vmx(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    vm_dir = tmp_path / "vms"
    vm_dir.mkdir()
    vmx = vm_dir / "ubuntu.vmx"
    vmx.write_text("# vmx\n", encoding="utf-8")

    monkeypatch.setattr(
        "community_vmware_desktop_hypervisor_mcp_server.inventory._default_search_paths",
        lambda: [vm_dir],
    )
    clear_inventory_cache()
    entries = discover_vms(refresh=True)
    assert len(entries) == 1
    assert entries[0].display_name == "ubuntu"
    assert Path(entries[0].vmx_path) == vmx.resolve()


def test_discover_vms_uses_cache(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    vm_dir = tmp_path / "cached"
    vm_dir.mkdir()
    vmx = vm_dir / "cached.vmx"
    vmx.write_text("# vmx\n", encoding="utf-8")
    calls = 0

    def fake_search_paths() -> list[Path]:
        nonlocal calls
        calls += 1
        return [vm_dir]

    monkeypatch.setattr(
        "community_vmware_desktop_hypervisor_mcp_server.inventory._default_search_paths",
        fake_search_paths,
    )
    clear_inventory_cache()

    first = discover_vms(refresh=True)
    second = discover_vms()

    assert len(first) == 1
    assert len(second) == 1
    assert calls == 1


def test_discover_vms_deduplicates_across_search_roots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    vm_dir = tmp_path / "dupe"
    vm_dir.mkdir()
    vmx = vm_dir / "ubuntu.vmx"
    vmx.write_text("# vmx\n", encoding="utf-8")

    monkeypatch.setattr(
        "community_vmware_desktop_hypervisor_mcp_server.inventory._default_search_paths",
        lambda: [vm_dir, vm_dir],
    )
    clear_inventory_cache()

    entries = discover_vms(refresh=True)
    assert len(entries) == 1
    assert entries[0].vmx_path == str(vmx.resolve())


def test_resolve_by_inventory_filename(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    vmx = tmp_path / "named-guest.vmx"
    vmx.write_text("# vmx\n", encoding="utf-8")

    monkeypatch.setattr(
        "community_vmware_desktop_hypervisor_mcp_server.inventory.discover_vms",
        lambda refresh=False: [
            VmEntry(
                id="abc123",
                display_name="named-guest",
                vmx_path=str(vmx.resolve()),
            )
        ],
    )

    assert resolve_vmx_path("named-guest.vmx") == vmx.resolve()
