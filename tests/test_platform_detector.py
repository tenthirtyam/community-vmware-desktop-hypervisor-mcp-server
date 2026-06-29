# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Tests for vmcli binary resolution."""

from __future__ import annotations

import subprocess as sp
from pathlib import Path
from unittest.mock import patch

import pytest

from community_vmware_desktop_hypervisor_mcp_server.platform_detector import (
    get_ui_open_args,
    is_hypervisor_ui_running,
    resolve_vmcli,
)


def test_resolve_vmcli_from_env(tmp_path: Path) -> None:
    binary = tmp_path / "vmcli"
    binary.write_text("", encoding="utf-8")
    with patch.dict("os.environ", {"VMCLI_PATH": str(binary)}, clear=False):
        assert resolve_vmcli() == binary.resolve()


def test_resolve_vmcli_env_missing_raises(tmp_path: Path) -> None:
    missing = tmp_path / "nope"
    with (
        patch.dict("os.environ", {"VMCLI_PATH": str(missing)}, clear=False),
        pytest.raises(FileNotFoundError, match="VMCLI_PATH"),
    ):
        resolve_vmcli()


def test_resolve_vmcli_via_which(tmp_path: Path) -> None:
    found = tmp_path / "vmcli"
    found.write_text("", encoding="utf-8")
    with (
        patch.dict("os.environ", {}, clear=False),
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.platform_detector.shutil.which",
            return_value=str(found),
        ),
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.platform_detector.DEFAULT_PATHS",
            {
                "darwin": tmp_path / "missing",
                "linux": tmp_path / "missing",
                "windows": tmp_path / "missing",
            },
        ),
    ):
        env = __import__("os").environ
        env.pop("VMCLI_PATH", None)
        assert resolve_vmcli() == found.resolve()


def test_resolve_vmcli_not_found() -> None:
    with (
        patch.dict("os.environ", {}, clear=False),
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.platform_detector.shutil.which",
            return_value=None,
        ),
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.platform_detector.DEFAULT_PATHS",
            {
                "darwin": Path("/nonexistent/vmcli"),
                "linux": Path("/nonexistent/vmcli"),
                "windows": Path("/nonexistent/vmcli"),
            },
        ),
        pytest.raises(FileNotFoundError, match="vmcli not found"),
    ):
        __import__("os").environ.pop("VMCLI_PATH", None)
        resolve_vmcli()


def test_resolve_vmcli_default_platform_path(tmp_path: Path) -> None:
    binary = tmp_path / "vmcli"
    binary.write_text("", encoding="utf-8")
    with (
        patch.dict("os.environ", {}, clear=False),
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.platform_detector.platform.system",
            return_value="Darwin",
        ),
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.platform_detector.DEFAULT_PATHS",
            {"darwin": binary},
        ),
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.platform_detector.shutil.which",
            return_value=None,
        ),
    ):
        __import__("os").environ.pop("VMCLI_PATH", None)
        assert resolve_vmcli() == binary.resolve()


# ---------------------------------------------------------------------------
# is_hypervisor_ui_running
# ---------------------------------------------------------------------------


def test_ui_running_darwin_pgrep_found() -> None:
    fake = sp.CompletedProcess(args=[], returncode=0)
    with (
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.platform_detector._platform_key",
            return_value="darwin",
        ),
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.platform_detector.shutil.which",
            return_value="/usr/bin/pgrep",
        ),
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.platform_detector.subprocess.run",
            return_value=fake,
        ),
    ):
        assert is_hypervisor_ui_running() is True


def test_ui_running_darwin_pgrep_not_found() -> None:
    fake = sp.CompletedProcess(args=[], returncode=1)
    with (
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.platform_detector._platform_key",
            return_value="darwin",
        ),
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.platform_detector.shutil.which",
            return_value="/usr/bin/pgrep",
        ),
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.platform_detector.subprocess.run",
            return_value=fake,
        ),
    ):
        assert is_hypervisor_ui_running() is False


def test_ui_running_windows_found() -> None:
    fake = sp.CompletedProcess(args=[], returncode=0, stdout='"vmware.exe","1234"\n')
    with (
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.platform_detector._platform_key",
            return_value="windows",
        ),
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.platform_detector.shutil.which",
            return_value="C:\\Windows\\System32\\tasklist.exe",
        ),
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.platform_detector.subprocess.run",
            return_value=fake,
        ),
    ):
        assert is_hypervisor_ui_running() is True


def test_ui_running_oserror_returns_false() -> None:
    with (
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.platform_detector._platform_key",
            return_value="linux",
        ),
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.platform_detector.shutil.which",
            return_value="/usr/bin/pgrep",
        ),
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.platform_detector.subprocess.run",
            side_effect=OSError("no proc fs"),
        ),
    ):
        assert is_hypervisor_ui_running() is False


# ---------------------------------------------------------------------------
# get_ui_open_args
# ---------------------------------------------------------------------------


def test_get_ui_open_args_darwin(tmp_path: Path) -> None:
    vmx = tmp_path / "test.vmwarevm" / "test.vmx"
    vmx.parent.mkdir()
    vmx.write_text("", encoding="utf-8")
    with patch(
        "community_vmware_desktop_hypervisor_mcp_server.platform_detector._platform_key",
        return_value="darwin",
    ):
        args = get_ui_open_args(vmx)
    assert args is not None
    assert args[0] == "open"
    assert "test.vmwarevm" in args[1]


def test_get_ui_open_args_linux_via_which(tmp_path: Path) -> None:
    vmx = tmp_path / "test.vmx"
    vmx.write_text("", encoding="utf-8")
    with (
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.platform_detector._platform_key",
            return_value="linux",
        ),
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.platform_detector.shutil.which",
            return_value="/usr/bin/vmware",
        ),
    ):
        args = get_ui_open_args(vmx)
    assert args is not None
    assert args[0] == "/usr/bin/vmware"
    assert str(vmx) in args


def test_get_ui_open_args_none_when_no_executable(tmp_path: Path) -> None:
    vmx = tmp_path / "test.vmx"
    vmx.write_text("", encoding="utf-8")
    with (
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.platform_detector._platform_key",
            return_value="linux",
        ),
        patch(
            "community_vmware_desktop_hypervisor_mcp_server.platform_detector.shutil.which",
            return_value=None,
        ),
    ):
        assert get_ui_open_args(vmx) is None
