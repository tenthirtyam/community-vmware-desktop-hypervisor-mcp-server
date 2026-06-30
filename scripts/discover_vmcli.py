# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

#!/usr/bin/env python3
"""Discover vmcli capabilities and write manifest.json + _generated_actions.py."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from community_vmware_desktop_hypervisor_mcp_server.discovery import (  # noqa: E402
    discover,
    render_generated_actions,
)
from community_vmware_desktop_hypervisor_mcp_server.platform_detector import (  # noqa: E402
    resolve_vmcli,
)

PKG = ROOT / "src" / "community_vmware_desktop_hypervisor_mcp_server"


def _write_line(text: str) -> None:
    """Write a single line to stdout."""
    sys.stdout.write(f"{text}\n")


def main() -> None:
    """Discover vmcli capabilities and regenerate checked-in artifacts."""
    parser = argparse.ArgumentParser(description="Discover vmcli and write artifacts")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=PKG / "manifest.json",
    )
    parser.add_argument(
        "--actions",
        type=Path,
        default=PKG / "_generated_actions.py",
    )
    args = parser.parse_args()
    vmcli = resolve_vmcli()
    manifest = asyncio.run(discover(vmcli))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    modules = manifest["modules"]
    if isinstance(modules, dict):
        args.actions.write_text(
            render_generated_actions(modules),
            encoding="utf-8",
        )
    mod_count = len(modules) if isinstance(modules, dict) else 0
    _write_line(f"Wrote {args.output} ({mod_count} modules)")
    _write_line(f"Wrote {args.actions}")


if __name__ == "__main__":
    main()
