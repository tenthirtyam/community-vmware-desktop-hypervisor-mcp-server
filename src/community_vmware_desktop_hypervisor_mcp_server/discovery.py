# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Discover vmcli capabilities from --help output."""

from __future__ import annotations

import asyncio
import platform
import re
from pathlib import Path
from typing import Any

MODULE_LINE = re.compile(r"^\t(\S+)\s*$")
MODULE_DESC = re.compile(r"^\t\s+(.+)$")
USAGE_CMD = re.compile(
    r"vmcli\s+\[<vmx location>\]\s+(\S+)\s+.*?\s+(\S+)\s+\[",
)
ARGS_SECTION = re.compile(r'^Arguments available to module "(\S+)":$')
ARG_ENTRY = re.compile(r"^\t(\S+)\s*$")
SECTION_END = re.compile(
    r"^(Global arguments:|Module:|Usage:|Arguments available to module |\s*$)",
)


async def run_help(vmcli: Path, args: list[str]) -> str:
    """Run a vmcli help command and return decoded output."""
    proc = await asyncio.create_subprocess_exec(
        str(vmcli),
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    text = (stdout or stderr).decode(errors="replace")
    if not text.strip() and proc.returncode != 0:
        msg = stderr.decode(errors="replace")
        raise RuntimeError(f"vmcli {' '.join(args)} failed: {msg}")
    return text


def parse_top_level(help_text: str) -> dict[str, str]:
    """Parse top-level module names and descriptions from vmcli help text."""
    modules: dict[str, str] = {}
    in_modules = False
    pending_name: str | None = None
    for line in help_text.splitlines():
        if line.strip() == "Available modules:":
            in_modules = True
            continue
        if not in_modules:
            continue
        m = MODULE_LINE.match(line)
        if m:
            pending_name = m.group(1)
            continue
        d = MODULE_DESC.match(line)
        if d and pending_name:
            modules[pending_name] = d.group(1).strip()
            pending_name = None
    return modules


def _parse_usage_commands(help_text: str, module: str) -> list[str]:
    """Extract command names from Usage lines for a module help page."""
    commands: list[str] = []
    for line in help_text.splitlines():
        um = USAGE_CMD.match(line)
        if um and um.group(1) == module:
            cmd = um.group(2)
            if cmd not in ("GLOBAL", "OPTIONS") and cmd not in commands:
                commands.append(cmd)
    return commands


def _parse_args_section_commands(help_text: str, module: str) -> list[str]:
    """Extract command names from the module arguments section."""
    commands: list[str] = []
    in_section = False
    for line in help_text.splitlines():
        am = ARGS_SECTION.match(line)
        if am:
            in_section = am.group(1) == module
            continue
        if not in_section:
            continue
        if SECTION_END.match(line) and line.strip():
            if not line.startswith("\t"):
                in_section = False
                continue
        em = ARG_ENTRY.match(line)
        if em:
            cmd = em.group(1)
            if cmd not in commands:
                commands.append(cmd)
    return commands


def parse_module_commands(help_text: str, module: str) -> list[str]:
    """Merge Usage lines and Arguments-available section (primary)."""
    merged: dict[str, None] = {}
    for cmd in _parse_args_section_commands(help_text, module):
        merged[cmd] = None
    for cmd in _parse_usage_commands(help_text, module):
        merged[cmd] = None
    return sorted(merged.keys(), key=str.lower)


def render_generated_actions(modules: dict[str, Any]) -> str:
    """Render the generated Literal aliases module from discovered commands."""
    lines = [
        "# Copyright (c) Ryan Johnson",
        "# SPDX-License-Identifier: MIT",
        "",
        '"""Auto-generated action Literals from vmcli discovery. Do not edit."""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Literal",
        "",
    ]
    for name in sorted(modules.keys()):
        mod = modules[name]
        commands = mod.get("commands", {}) if isinstance(mod, dict) else {}
        if not isinstance(commands, dict) or not commands:
            continue
        type_name = f"{name}Action"
        literals = ", ".join(repr(c) for c in sorted(commands.keys(), key=str.lower))
        lines.append(f"{type_name} = Literal[{literals}]")
        lines.append("")
    return "\n".join(lines) + "\n"


def action_doc(module: str, commands: list[str]) -> str:
    """Build a compact tool docstring preview from discovered commands."""
    preview = ", ".join(commands[:12])
    suffix = "..." if len(commands) > 12 else ""
    return f"vmcli {module} module. Valid actions: {preview}{suffix}"


async def discover(vmcli: Path) -> dict[str, Any]:
    """Discover vmcli modules and commands by walking help output."""
    root_help = await run_help(vmcli, ["--help"])
    modules_meta = parse_top_level(root_help)
    modules: dict[str, Any] = {}
    for name, description in modules_meta.items():
        mod_help = await run_help(vmcli, [name, "--help"])
        commands = parse_module_commands(mod_help, name)
        modules[name] = {
            "description": description,
            "commands": {cmd: {} for cmd in commands},
        }
    return {
        "version": "1.0",
        "platform": platform.system(),
        "binary": str(vmcli),
        "global_args": {
            "vmx": {"required_for_vm_ops": True, "position": "first_or_last"},
            "verbose": "--verbose",
        },
        "modules": modules,
    }
