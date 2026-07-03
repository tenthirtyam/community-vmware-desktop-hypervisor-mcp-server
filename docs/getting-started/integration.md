# Integration

Connect **community-vmware-desktop-hypervisor-mcp-server** to your MCP host. Transport is **stdio** only: the server must run where VMware is installed.

## VS Code

- **Requires:** VS Code **1.106+**.
- **Config:** `.vscode/mcp.json` in workspace.

### `pip`

```json
{
  "servers": {
    "community-vmware-desktop-hypervisor-mcp-server": {
      "type": "stdio",
      "command": "community-vmware-desktop-hypervisor-mcp-server",
      "env": {
        "VMCLI_OUTPUT_FORMAT": "json"
      }
    }
  }
}
```

### `uv`

```json
{
  "servers": {
    "community-vmware-desktop-hypervisor-mcp-server": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run", "--with", "community-vmware-desktop-hypervisor-mcp-server",
        "community-vmware-desktop-hypervisor-mcp-server"
      ]
    }
  }
}
```

### Development (This Repository)

1. `make install-vscode`
2. Open folder in VS Code
3. Enable via **MCP: List Servers** or Copilot MCP settings

Project file: [`.vscode/mcp.json`](../../.vscode/mcp.json)

More: [VS Code MCP documentation](https://code.visualstudio.com/docs/copilot/customization/mcp-servers)

### Verify (VS Code)

1. Restart VS Code
2. **MCP: List Servers**: server running
3. Copilot Chat (Agent mode): tools picker shows `vm_list`, etc.

## Cursor

**Config:** `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project)

### `pip`

```json
{
  "mcpServers": {
    "community-vmware-desktop-hypervisor-mcp-server": {
      "command": "community-vmware-desktop-hypervisor-mcp-server",
      "env": {
        "VMCLI_OUTPUT_FORMAT": "json"
      }
    }
  }
}
```

### `uv`

```json
{
  "mcpServers": {
    "community-vmware-desktop-hypervisor-mcp-server": {
      "command": "uv",
      "args": [
        "run", "--with", "community-vmware-desktop-hypervisor-mcp-server",
        "community-vmware-desktop-hypervisor-mcp-server"
      ]
    }
  }
}
```

### Development (This Repository)

1. `make install-cursor`
2. Open the repo in Cursor
3. Enable **community-vmware-desktop-hypervisor-mcp-server** under **Settings → Tools & MCP**

Uses [`.cursor/mcp.json`](../../.cursor/mcp.json) with `${workspaceFolder}` and a shell wrapper for paths with spaces.

### Verify (Cursor)

1. Restart Cursor
2. **Settings → Tools & MCP**: green indicator on the server
3. Test: *"List VMware VMs on this machine"*

### Troubleshooting (Cursor)

| Issue                   | Fix                                                                                 |
| ----------------------- | ----------------------------------------------------------------------------------- |
| Server won't start      | Confirm `community-vmware-desktop-hypervisor-mcp-server` on `PATH` or use uv config |
| Tools missing           | Restart; re-enable in MCP settings                                                  |
| Paths with spaces       | Use project `.cursor/mcp.json` shell wrapper                                        |

## Claude Desktop

| OS      | Config Path                                                       |
| ------- | ----------------------------------------------------------------- |
| macOS   | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json`                     |
| Linux   | `~/.config/Claude/claude_desktop_config.json`                     |

Restart Claude Desktop after editing.

### `pip`

```json
{
  "mcpServers": {
    "community-vmware-desktop-hypervisor-mcp-server": {
      "command": "community-vmware-desktop-hypervisor-mcp-server",
      "env": {
        "VMCLI_PATH": "/Applications/VMware Fusion.app/Contents/Public/vmcli",
        "VMCLI_SEARCH_PATHS": "/Applications/Virtual Machines"
      }
    }
  }
}
```

### Python Module (venv)

```json
{
  "mcpServers": {
    "community-vmware-desktop-hypervisor-mcp-server": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["-m", "community_vmware_desktop_hypervisor_mcp_server.server"],
      "env": {
        "VMCLI_PATH": "/Applications/VMware Fusion.app/Contents/Public/vmcli"
      }
    }
  }
}
```

**Windows:** use `C:\\path\\to\\.venv\\Scripts\\python.exe` and Workstation `vmcli.exe` path.

### Verify (Claude Desktop)

Invoke **`vm_discover_capabilities`** and **`vm_list`**. Logs (macOS): `~/Library/Logs/Claude/mcp-server-*.log`

## Claude Code

Run in your **system terminal** ([Claude Code MCP docs](https://docs.claude.com/en/docs/claude-code/mcp)):

```bash
# pip
claude mcp add community-vmware-desktop-hypervisor-mcp-server -s user -- community-vmware-desktop-hypervisor-mcp-server

# uv
claude mcp add community-vmware-desktop-hypervisor-mcp-server -s user -- \
  uv run --with community-vmware-desktop-hypervisor-mcp-server community-vmware-desktop-hypervisor-mcp-server

# with env
claude mcp add community-vmware-desktop-hypervisor-mcp-server -s user \
  -e VMCLI_PATH="/Applications/VMware Fusion.app/Contents/Public/vmcli" \
  -- community-vmware-desktop-hypervisor-mcp-server
```

Verify:

```bash
claude mcp list
claude mcp get community-vmware-desktop-hypervisor-mcp-server
```

## Paths With Spaces

```json
{
  "mcpServers": {
    "community-vmware-desktop-hypervisor-mcp-server": {
      "command": "/bin/sh",
      "args": [
        "-c",
        "WF=\"$HOME/path/to/community-vmware-desktop-hypervisor-mcp-server\"; export PYTHONPATH=\"$WF/src\"; exec \"$WF/.venv/bin/python\" -m community_vmware_desktop_hypervisor_mcp_server.server"
      ]
    }
  }
}
```

See [`.cursor/mcp.json`](../../.cursor/mcp.json) for the `${workspaceFolder}` variant.
