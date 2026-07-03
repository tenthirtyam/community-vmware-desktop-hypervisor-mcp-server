---
icon: octicons/rocket-16
---

# Getting Started

End-to-end path from VMware install to your first MCP tool call.

## 1. Prerequisites

1. **VMware Fusion** (macOS) or **VMware Workstation** (Windows/Linux) on the machine that runs the MCP server
2. **Python 3.12+** or **[uv](https://docs.astral.sh/uv/)**
3. An **MCP host**: see the [Host Support](integration.md#host-support) matrix

Verify VMware:

```bash
vmcli --help
```

Default `vmcli` paths and overrides: [Installation](installation.md) · [Configuration](configuration.md)

## 2. Install the MCP Server

=== "pip"

    ```bash
    pip install community-vmware-desktop-hypervisor-mcp-server
    community-vmware-desktop-hypervisor-mcp-server --help
    ```

=== "uv"

    No prior install: [uv](https://docs.astral.sh/uv/) fetches the package on first MCP host launch:

    ```bash
    uv run --with community-vmware-desktop-hypervisor-mcp-server community-vmware-desktop-hypervisor-mcp-server --help
    ```

=== "From Source"

    ```bash
    git clone https://github.com/tenthirtyam/community-vmware-desktop-hypervisor-mcp-server.git
    cd community-vmware-desktop-hypervisor-mcp-server
    make venv && make install-dev
    ```

## 3. Configure Your MCP Host

Per-host JSON, verify steps, and troubleshooting: **[Integration](integration.md)**

| Host                         | Section                                               |
| ---------------------------- | ----------------------------------------------------- |
| Cursor                       | [Integration → Cursor](integration.md#cursor)         |
| VS Code                      | [Integration → VS Code](integration.md#vs-code)       |
| Claude Desktop & Claude Code | [Integration → Claude](integration.md#claude-desktop) |
## 4. Verify the Connection

1. Restart your MCP host completely
2. Call **`vm_discover_capabilities`**: confirms `vmcli` is found
3. Call **`vm_list`**: returns JSON inventory of `.vmx` files on disk

If a tool returns `isError: true`, read the text content. See [Error Handling](error-handling.md).

## 5. First Tool Calls

### List Virtual Machines

Tool: **`vm_list`** (no parameters).

```json
[
  {
    "id": "1ee0922d292f",
    "display_name": "Ubuntu 64-bit Arm 26.04",
    "vmx_path": "/Applications/Virtual Machines/.../Ubuntu 64-bit Arm 26.04.vmx"
  }
]
```

### Query Power State

Tool: **`vm_power_management`**. Module tools require a **`params`** object:

```json
{
  "params": {
    "action": "query",
    "vmx_path": "Ubuntu 64-bit Arm 26.04"
  }
}
```

`vmx_path` accepts an absolute `.vmx` path, inventory **`display_name`**, or inventory **`id`** from `vm_list`.

### Discover Capabilities

Tool: **`vm_discover_capabilities`**. Returns a JSON manifest of `vmcli` modules and commands for your VMware version.

## Next Steps

- [Configuration](configuration.md): `VMCLI_PATH`, `VMCLI_SEARCH_PATHS`, timeouts
- [MCP Tools](mcp-tools.md): full tool list and typed parameters
- [Troubleshooting](troubleshooting.md): when something breaks
