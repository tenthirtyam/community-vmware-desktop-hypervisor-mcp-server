# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Tests for server_common helpers."""

from __future__ import annotations

from mcp.types import CallToolResult, TextContent

from community_vmware_desktop_hypervisor_mcp_server.server_common import (
    VmCliResult,
    _is_progress_only_stderr,  # pyright: ignore[reportPrivateUsage]
    tool_result_from_vmcli,
)

# ---------------------------------------------------------------------------
# _is_progress_only_stderr
# ---------------------------------------------------------------------------

_SUSPEND_STDERR = (
    "Progress: 0% (4194304 out of 4294967296)\n"
    "Progress: 47% (2021654528 out of 4294967296)\n"
    "Progress: 97% (4169138176 out of 4294967296)\n"
)

_START_STDERR = (
    "Progress: 0% (0 out of 229)\n"
    "Progress: 47% (110 out of 233)\n"
    "Progress: 81% (189 out of 233)\n"
    "Progress: 82% (192 out of 233)\n"
)


def test_progress_only_suspend_stderr() -> None:
    assert _is_progress_only_stderr(_SUSPEND_STDERR) is True


def test_progress_only_start_stderr() -> None:
    assert _is_progress_only_stderr(_START_STDERR) is True


def test_progress_only_empty_stderr_is_false() -> None:
    assert _is_progress_only_stderr("") is False


def test_progress_only_whitespace_only_is_false() -> None:
    assert _is_progress_only_stderr("   \n  \n") is False


def test_progress_only_real_error_is_false() -> None:
    assert _is_progress_only_stderr("vmcli: VM is powered off") is False


def test_progress_only_mixed_stderr_is_false() -> None:
    mixed = _SUSPEND_STDERR + "vmcli: error writing suspend file\n"
    assert _is_progress_only_stderr(mixed) is False


# ---------------------------------------------------------------------------
# tool_result_from_vmcli
# ---------------------------------------------------------------------------


def _make_result(ok: bool, stdout: str = "", stderr: str = "", rc: int = 0) -> VmCliResult:
    return VmCliResult(ok=ok, stdout=stdout, stderr=stderr, returncode=rc, command=[])


def _text(result: CallToolResult) -> str:
    """Assert the first content item is TextContent and return its text."""
    item = result.content[0]
    assert isinstance(item, TextContent)
    return item.text


def test_success_result_is_not_error() -> None:
    result = tool_result_from_vmcli(_make_result(ok=True, stdout='{"state":"on"}'))
    assert result.isError is not True
    assert _text(result) == '{"state":"on"}'


def test_real_failure_is_error() -> None:
    result = tool_result_from_vmcli(_make_result(ok=False, stderr="VM is powered off", rc=1))
    assert result.isError is True
    assert "powered off" in _text(result)


def test_progress_only_stderr_not_flagged_as_error() -> None:
    """vmcli Suspend/Start exits non-zero with progress-only stderr — must not be isError."""
    result = tool_result_from_vmcli(_make_result(ok=False, stderr=_SUSPEND_STDERR, rc=141))
    assert result.isError is not True


def test_progress_only_stderr_surfaced_in_text() -> None:
    result = tool_result_from_vmcli(_make_result(ok=False, stderr=_START_STDERR, rc=141))
    assert "Progress" in _text(result)


def test_success_with_stdout_prefers_stdout() -> None:
    result = tool_result_from_vmcli(_make_result(ok=True, stdout="output", stderr=_SUSPEND_STDERR))
    assert _text(result) == "output"
