# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Shared types and constants for the MCP server."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from mcp.types import CallToolResult, TextContent

VmxPosition = Literal["first", "last"]

# VMCLI_OUTPUT_FORMAT env -> vmcli -f <name> (Fusion/Workstation vmcli uses string enums)
OUTPUT_FORMAT_MAP: dict[str, str] = {
    "json": "json",
    "yaml": "yaml",
    "toml": "toml",
}

# Legacy env value; current vmcli only accepts json, yaml, toml
OUTPUT_FORMAT_ALIASES: dict[str, str] = {
    "text": "json",
}

QUERY_ACTIONS = frozenset({"query", "Query"})

# vmcli writes "Progress: N% (X out of Y)" lines to stderr for long-running
# power operations (Suspend, Start/resume).  These are informational, not errors.
_PROGRESS_LINE_RE = re.compile(r"^Progress:\s+\d+%\s+\(\d+\s+out\s+of\s+\d+\)\s*$")


def _is_progress_only_stderr(stderr: str) -> bool:
    """Return True when every non-empty stderr line is a vmcli progress message."""
    lines = [ln for ln in stderr.splitlines() if ln.strip()]
    return bool(lines) and all(_PROGRESS_LINE_RE.match(ln) for ln in lines)


@dataclass(frozen=True)
class VmCliResult:
    """Result of a vmcli subprocess invocation."""

    ok: bool
    stdout: str
    stderr: str
    returncode: int
    command: list[str]

    @property
    def text(self) -> str:
        """Return stdout on success or a normalized VMware error string."""
        if self.ok:
            return self.stdout
        msg = self.stderr.strip() or self.stdout.strip()
        if msg:
            return f"VMware vmcli error: {msg}"
        return f"VMware vmcli error: vmcli exited with code {self.returncode}"


def tool_result_from_vmcli(result: VmCliResult) -> CallToolResult:
    """Map vmcli result to MCP CallToolResult (isError=True on failure).

    vmcli exits non-zero with progress-only stderr for long-running power
    operations (Suspend, Start/resume).  Treat those as success and surface
    the progress lines as informational text.
    """
    if result.ok or _is_progress_only_stderr(result.stderr):
        text = result.stdout if result.stdout else result.stderr
        return CallToolResult(content=[TextContent(type="text", text=text)])
    return CallToolResult(
        content=[TextContent(type="text", text=result.text)],
        isError=True,
    )
