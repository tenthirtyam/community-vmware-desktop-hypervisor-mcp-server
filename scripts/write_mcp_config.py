# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

#!/usr/bin/env python3
"""Create or update local MCP host config for this repository."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SERVER_NAME = "community-vmware-desktop-hypervisor-mcp-server"
SERVER_COMMAND = (
    'WF="${workspaceFolder}"; export PYTHONPATH="$WF/src"; '
    'exec "$WF/.venv/bin/python" -m community_vmware_desktop_hypervisor_mcp_server.server'
)


def _load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        msg = f"Expected JSON object in {path}"
        raise TypeError(msg)
    return data


def _cursor_server() -> dict[str, Any]:
    return {
        "command": "/bin/sh",
        "args": ["-c", SERVER_COMMAND],
        "env": {
            "VMCLI_OUTPUT_FORMAT": "json",
        },
    }


def _vscode_server() -> dict[str, Any]:
    return {
        "type": "stdio",
        "command": "/bin/sh",
        "args": ["-c", SERVER_COMMAND],
        "env": {
            "VMCLI_OUTPUT_FORMAT": "json",
        },
    }


def _write_config(host: str, path: Path) -> None:
    config = _load_config(path)
    collection_key = "mcpServers" if host == "cursor" else "servers"
    server = _cursor_server() if host == "cursor" else _vscode_server()

    existing_collection = config.get(collection_key)
    if existing_collection is None:
        collection: dict[str, Any] = {}
    elif isinstance(existing_collection, dict):
        collection = existing_collection
    else:
        msg = f"Expected '{collection_key}' to be a JSON object in {path}"
        raise ValueError(msg)

    collection[SERVER_NAME] = server
    config[collection_key] = collection

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)
        handle.write("\n")

    print(f"Updated {path}")


EXPECTED_ARG_COUNT = 3


def main() -> int:
    if len(sys.argv) != EXPECTED_ARG_COUNT:
        print("Usage: write_mcp_config.py <cursor|vscode> <path>", file=sys.stderr)
        return 1

    host = sys.argv[1]
    output_path = Path(sys.argv[2])

    if host not in {"cursor", "vscode"}:
        print(f"Unsupported host: {host}", file=sys.stderr)
        return 1

    try:
        _write_config(host, output_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Failed to write {output_path}: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
