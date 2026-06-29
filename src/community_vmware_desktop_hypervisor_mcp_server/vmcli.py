# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Build vmcli argv and run subprocesses asynchronously."""

from __future__ import annotations

import asyncio
from pathlib import Path

from .config import get_settings
from .context import get_runner
from .platform_detector import resolve_vmcli
from .server_common import (
    QUERY_ACTIONS,
    VmCliResult,
    VmxPosition,
)


class CommandBuilder:
    """Assemble vmcli command-line argument lists."""

    def __init__(
        self,
        module: str,
        action: str,
        *,
        vmx_path: Path | None = None,
        command_args: list[str] | None = None,
        vmx_position: VmxPosition = "first",
        verbose: bool = False,
        extra_format_args: list[str] | None = None,
    ) -> None:
        """Store the inputs needed to build one vmcli command line."""
        self.module = module
        self.action = action
        self.vmx_path = vmx_path
        self.command_args = list(command_args or [])
        self.vmx_position = vmx_position
        self.verbose = verbose
        self.extra_format_args = list(extra_format_args or [])

    def build(self) -> list[str]:
        """Return the final vmcli argv for this invocation."""
        core: list[str] = []
        if self.vmx_path is not None and self.vmx_position == "first":
            core.append(str(self.vmx_path))
        core.extend([self.module, self.action])
        if self.verbose:
            core.append("--verbose")
        core.extend(self.extra_format_args)
        core.extend(self.command_args)
        if self.vmx_path is not None and self.vmx_position == "last":
            core.append(str(self.vmx_path))
        return core


class VmCliRunner:
    """Execute vmcli via asyncio subprocess."""

    def __init__(self, binary: Path | None = None) -> None:
        """Initialize the runner with an optional pre-resolved binary path."""
        self._binary = binary

    @property
    def binary(self) -> Path:
        """Return the resolved vmcli binary path."""
        if self._binary is None:
            self._binary = resolve_vmcli()
        return self._binary

    async def run(self, argv: list[str]) -> VmCliResult:
        """Execute vmcli with argv and capture structured output."""
        settings = get_settings()
        proc = await asyncio.create_subprocess_exec(
            str(self.binary),
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(),
                timeout=settings.vmcli_timeout_seconds,
            )
        except TimeoutError:
            proc.kill()
            await proc.wait()
            timeout = settings.vmcli_timeout_seconds
            return VmCliResult(
                ok=False,
                stdout="",
                stderr=f"vmcli timed out after {timeout}s",
                returncode=-1,
                command=argv,
            )
        stdout = stdout_b.decode(errors="replace")
        stderr = stderr_b.decode(errors="replace")
        _rc = proc.returncode
        rc: int = _rc if _rc is not None else -1
        return VmCliResult(
            ok=rc == 0,
            stdout=stdout,
            stderr=stderr,
            returncode=rc,
            command=argv,
        )


def format_args_for_query(action: str) -> list[str]:
    """Return default output-format flags for query-style actions."""
    if action not in QUERY_ACTIONS:
        return []
    settings = get_settings()
    return ["-f", str(settings.vmcli_format_flag)]


def _query_format_args(action: str, output_format: str | None) -> list[str]:
    """Return query output-format flags, honoring explicit overrides."""
    if action not in QUERY_ACTIONS:
        return []
    if output_format is not None:
        return ["-f", output_format]
    return format_args_for_query(action)


async def run_module_command(
    module: str,
    action: str,
    *,
    vmx_path: Path | None = None,
    command_args: list[str] | None = None,
    vmx_position: VmxPosition = "first",
    verbose: bool = False,
    output_format: str | None = None,
) -> VmCliResult:
    """Build and run a vmcli module command through the shared runner."""
    builder = CommandBuilder(
        module,
        action,
        vmx_path=vmx_path,
        command_args=command_args,
        vmx_position=vmx_position,
        verbose=verbose,
        extra_format_args=_query_format_args(action, output_format),
    )
    return await get_runner().run(builder.build())
