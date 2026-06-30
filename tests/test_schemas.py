# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Tests for Pydantic tool schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from community_vmware_desktop_hypervisor_mcp_server.inventory import resolve_vmx_path
from community_vmware_desktop_hypervisor_mcp_server.schemas import (
    DiskParams,
    GuestParams,
    PowerParams,
    SnapshotParams,
    VmCreateParams,
    build_guest_extra_args,
    build_power_extra_args,
    build_snapshot_extra_args,
)


def test_disk_extend_validates() -> None:
    params = DiskParams(action="Extend", vmx_path="/tmp/a.vmx")
    assert params.action == "Extend"


def test_disk_invalid_action_rejected() -> None:
    with pytest.raises(ValidationError):
        DiskParams(action="NotARealCommand", vmx_path="/tmp/a.vmx")  # type: ignore[arg-type]


def test_power_requires_vmx() -> None:
    with pytest.raises(ValidationError, match="vmx_path"):
        PowerParams(action="query")


def test_power_accepts_inventory_alias() -> None:
    params = PowerParams(action="query", vmx_path="test-vm")
    assert params.vmx_path == "test-vm"


def test_resolve_vmx_path_rejects_non_vmx_file(tmp_path) -> None:
    not_vmx = tmp_path / "notvmx"
    not_vmx.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match=r"\.vmx"):
        resolve_vmx_path(str(not_vmx))


def test_vm_create_no_vmx() -> None:
    params = VmCreateParams(name="test", dirpath="/tmp/vms")
    assert params.action == "Create"


def test_build_power_extra_args_stop_default_op_type() -> None:
    args = build_power_extra_args(
        PowerParams(action="Stop", vmx_path="/tmp/a.vmx"),
    )
    assert args == ["-o", "trySoft"]


def test_build_power_extra_args_stop_respects_command_args() -> None:
    args = build_power_extra_args(
        PowerParams(
            action="Stop",
            vmx_path="/tmp/a.vmx",
            command_args=["-o", "hard"],
        ),
    )
    assert args == ["-o", "hard"]


def test_build_power_extra_args_paused() -> None:
    params = PowerParams(action="Start", vmx_path="/tmp/a.vmx", paused=True)
    assert "--paused" in build_power_extra_args(params)


def test_build_snapshot_extra_args_take() -> None:
    params = SnapshotParams(
        action="Take",
        vmx_path="/tmp/a.vmx",
        snapshot_name="s1",
        include_memory=True,
        description="desc",
    )
    args = build_snapshot_extra_args(params)
    assert "--memory" in args
    assert "--description" in args
    assert "desc" in args
    assert "s1" in args


# ---------------------------------------------------------------------------
# GuestParams / build_guest_extra_args
# ---------------------------------------------------------------------------


def test_guest_run_requires_username() -> None:
    with pytest.raises(ValidationError, match="username"):
        GuestParams(
            action="run",
            vmx_path="/tmp/a.vmx",
            password="pass",
            program="/bin/uname",
        )


def test_guest_run_requires_password() -> None:
    with pytest.raises(ValidationError, match="password"):
        GuestParams(
            action="run",
            vmx_path="/tmp/a.vmx",
            username="user",
            program="/bin/uname",
        )


def test_guest_run_requires_program() -> None:
    with pytest.raises(ValidationError, match="program"):
        GuestParams(
            action="run",
            vmx_path="/tmp/a.vmx",
            username="user",
            password="pass",
        )


def test_guest_non_run_does_not_require_credentials() -> None:
    params = GuestParams(action="query", vmx_path="/tmp/a.vmx")
    assert params.action == "query"


def test_build_guest_extra_args_run_basic() -> None:
    params = GuestParams(
        action="run",
        vmx_path="/tmp/a.vmx",
        username="user",
        password="pass",
        program="/bin/uname",
        program_args=["-a"],
    )
    args = build_guest_extra_args(params)
    assert args == ["-u", "user", "-p", "pass", "/bin/uname", "-a"]


def test_build_guest_extra_args_run_shell_command() -> None:
    params = GuestParams(
        action="run",
        vmx_path="/tmp/a.vmx",
        username="user",
        password="pass",
        program="/bin/sh",
        program_args=["-c", "uname -a > /tmp/uname.txt"],
    )
    args = build_guest_extra_args(params)
    assert args == ["-u", "user", "-p", "pass", "/bin/sh", "-c", "uname -a > /tmp/uname.txt"]


def test_build_guest_extra_args_run_options() -> None:
    params = GuestParams(
        action="run",
        vmx_path="/tmp/a.vmx",
        username="user",
        password="pass",
        program="/bin/sh",
        no_wait=True,
        interactive=True,
        working_dir="/tmp",
        environment=["FOO=bar"],
    )
    args = build_guest_extra_args(params)
    assert "--noWait" in args
    assert "--interactive" in args
    assert "-w" in args
    assert "/tmp" in args
    assert "-e" in args
    assert "FOO=bar" in args


def test_build_guest_extra_args_non_run_uses_command_args() -> None:
    params = GuestParams(
        action="query",
        vmx_path="/tmp/a.vmx",
        command_args=["-f", "json"],
    )
    args = build_guest_extra_args(params)
    assert args == ["-f", "json"]
