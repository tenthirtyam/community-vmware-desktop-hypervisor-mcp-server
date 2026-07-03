# Configuration

Configure the server with **environment variables** in your MCP host configuration (`env` block).

Variables are read when the server process starts.

| Variable                | Required | Default          | Description                                                     |
| ----------------------- | -------- | ---------------- | --------------------------------------------------------------- |
| `VMCLI_LOG_LEVEL`       | No       | `WARNING`        | Python logging level                                            |
| `VMCLI_OUTPUT_FORMAT`   | No       | `json`           | Query format: `json`, `yaml`, `toml` (`text` aliases to `json`) |
| `VMCLI_PATH`            | No       | Platform default | Absolute path to `vmcli`                                        |
| `VMCLI_SEARCH_PATHS`    | No       | Platform default | Colon-separated directories scanned by `vm_list`                |
| `VMCLI_TIMEOUT_SECONDS` | No       | `120`            | Max seconds per `vmcli` subprocess                              |

## Example

**VS Code**: `.vscode/mcp.json`:

```json
{
  "servers": {
    "community-vmware-desktop-hypervisor-mcp-server": {
      "type": "stdio",
      "command": "community-vmware-desktop-hypervisor-mcp-server",
      "env": {
        "VMCLI_PATH": "/Applications/VMware Fusion.app/Contents/Public/vmcli",
        "VMCLI_SEARCH_PATHS": "/Applications/Virtual Machines:/Users/example/Virtual Machines.localized",
        "VMCLI_OUTPUT_FORMAT": "json",
        "VMCLI_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Default Paths

Default paths for `vmcli`.

| OS       | Platform           | Default Path                                                 |
| -------- | ------------------ | ------------------------------------------------------------ |
| macOS    | VMware Fusion      | `/Applications/VMware Fusion.app/Contents/Public/vmcli`      |
| Windows  | VMware Workstation | `C:\Program Files (x86)\VMware\VMware Workstation\vmcli.exe` |
| Linux    | VMware Workstation | `/usr/bin/vmcli`                                             |

If the default file is missing, set `VMCLI_PATH`. The server fails at startup with a clear error
when `vmcli` cannot be resolved.

## Search Paths

When `VMCLI_SEARCH_PATHS` is unset, macOS also scans:

- `/Applications/Virtual Machines`
- `~/Virtual Machines.localized`
- `~/Documents/Virtual Machines.localized`

Windows and Linux scan common home-directory virtual machine folders.

Set `VMCLI_SEARCH_PATHS` explicitly when virtual machines reside elsewhere.

Use **absolute paths** in MCP host `env` blocks. Tilde (`~`) is **not** expanded by the server.

## Path Resolution

For tools that require a virtual machine:

1. Absolute path to a `.vmx` file
2. Inventory **`id`** from `vm_list`
3. Inventory **`display_name`** from `vm_list` (case-insensitive)

Exceptions: no `vmx_path` required:

- `VM` → `Create` (new VM)
- `VMTemplate` → `Deploy` (from template path)
