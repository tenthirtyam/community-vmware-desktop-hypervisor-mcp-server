# Installation

## Install the MCP Server

### Using `pip`

```bash
pip install community-vmware-desktop-hypervisor-mcp-server
```

| Item               | Value                                                   |
| ------------------ | ------------------------------------------------------- |
| PyPI Package       | `community-vmware-desktop-hypervisor-mcp-server`        |
| Console Entrypoint | `community-vmware-desktop-hypervisor-mcp-server`        |
| Python Module      | `community_vmware_desktop_hypervisor_mcp_server.server` |
| MCP Server Name    | `community-vmware-desktop-hypervisor-mcp-server`        |
| Minimum Python     | 3.12                                                    |

### Using `uv`

Run without a persistent install:

```bash
uv run --with community-vmware-desktop-hypervisor-mcp-server community-vmware-desktop-hypervisor-mcp-server
```

Or use `uvx` as a shorthand:

```bash
uvx community-vmware-desktop-hypervisor-mcp-server
```

### Using `git`

```bash
VERSION=v0.1.0
git clone https://github.com/tenthirtyam/community-vmware-desktop-hypervisor-mcp-server.git
cd community-vmware-desktop-hypervisor-mcp-server
git checkout tags/$VERSION
make venv && make install-dev
```

## Install `vmcli`

Install VMware Fusion or Workstation on the **same machine** as the MCP server.

| Platform | Product            | Default Path                                                 |
| -------- | ------------------ | ------------------------------------------------------------ |
| macOS    | VMware Fusion      | `/Applications/VMware Fusion.app/Contents/Public/vmcli`      |
| Windows  | VMware Workstation | `C:\Program Files (x86)\VMware\VMware Workstation\vmcli.exe` |
| Linux    | VMware Workstation | `/usr/bin/vmcli`                                             |
Verify:

```bash
vmcli --help
```

Override with `VMCLI_PATH` if the binary is elsewhere. Refer to [Configuration](configuration.md).

## Verify Installation

After install, run the server directly. It will block waiting for MCP host input over stdio and no
output is expected:

```bash
community-vmware-desktop-hypervisor-mcp-server
```

In an MCP host, call **`vm_discover_capabilities`** to confirm startup and `vmcli` resolution.

## Next Step

Configure your MCP host: [Integration](integration.md)
