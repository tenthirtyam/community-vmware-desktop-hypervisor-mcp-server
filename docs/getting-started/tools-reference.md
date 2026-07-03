# Tools Reference

All capabilities are exposed as **Tools**.

Tools are grouped by `vmcli` **module** (not one tool per subcommand). Pass the subcommand name in `action` using exact vmcli casing.

## Calling Tools

| Tool                       | Arguments                  |
| -------------------------- | -------------------------- |
| `vm_list`                  | None                       |
| `vm_discover_capabilities` | None                       |
| All other tools            | Single **`params`** object |

```json
{
  "params": {
    "action": "query",
    "vmx_path": "ubuntu-2604-arm"
  }
}
```

## Inventory and Discovery

| Tool                       | Description                                                                     |
| -------------------------- | ------------------------------------------------------------------------------- |
| `vm_list`                  | Scan configured paths for `.vmx` files; return `id`, `display_name`, `vmx_path`   |
| `vm_discover_capabilities` | Run live `vmcli --help` discovery; return capability manifest JSON              |

## Lifecycle

| Tool                     | `vmcli` Module | Typical Actions                                                  |
| ------------------------ | -------------- | ---------------------------------------------------------------- |
| `vm_lifecycle`           | VM             | `Create` (new VM; no existing `.vmx`)                            |
| `vm_power_management`    | Power          | `query`, `Start`, `Stop`, `Pause`, `Reset`, `Suspend`, `Unpause` |
| `vm_snapshot_management` | Snapshot       | `query`, `Take`, `Delete`, `Revert`, `Clone`                     |
| `vm_template_management` | VMTemplate     | `Create`, `Deploy`                                               |

`vm_power_management` with `action: "Stop"` defaults to `stop_op_type: "trySoft"` (guest shutdown). Override with `stop_op_type` or `command_args`.

## Hardware and Configuration

| Tool                     | `vmcli` Module | Notes                                           |
| ------------------------ | -------------- | ----------------------------------------------- |
| `vm_chipset_operations`  | Chipset        | `query`, `SetVCpuCount`, `SetMemSize`, …        |
| `vm_config_params`        | ConfigParams    | `query`, `SetEntry`                             |
| `vm_disk_operations`     | Disk           | Many disk actions; use `command_args` for flags  |
| `vm_ethernet_operations` | Ethernet       | Adapter create/modify/remove                    |
| `vm_nvme_operations`     | Nvme           | NVMe controllers and disks                      |
| `vm_sata_operations`     | Sata           | SATA controllers                                |
| `vm_serial_operations`   | Serial         | Uses `Query` (capital **Q**) for query          |

## Guest and Host Integration

| Tool                    | `vmcli` Module | Notes                                     |
| ----------------------- | -------------- | ----------------------------------------- |
| `vm_guest_operations`   | Guest          | Guest must be powered on for many actions |
| `vm_hgfs_operations`    | HGFS           | Shared folders                            |
| `vm_mks_operations`     | MKS            | Screenshots, display, keyboard/mouse      |
| `vm_tools_management`   | Tools          | `Install`, `Upgrade`, `Query`             |
| `vm_vprobes_operations` | VProbes        | Uses `Query` for query                    |

## Common Parameters

Fields on the `params` object for module tools:

| Field           | Type                             | Description                                           |
| --------------- | -------------------------------- | ----------------------------------------------------- |
| `action`        | `string`                         | `vmcli` subcommand (required)                         |
| `command_args`  | `string[]`                       | Extra flags and positionals passed to `vmcli`          |
| `output_format` | `"json"` \| `"yaml"` \| `"toml"` | For `query` / `Query` actions only                    |
| `verbose`       | `boolean`                        | Append `--verbose` to vmcli                           |
| `vmx_path`      | `string`                         | `.vmx` path, inventory `id`, or `display_name`        |
| `vmx_position`  | `"first"` \| `"last"`             | Where to place `vmx_path` on argv (default `"first"`)  |

### Typed Fields

**`vm_guest_operations`** — `run` action only

| Field            | Type       | Applies To | Description                                       |
| ---------------- | ---------- | ---------- | ------------------------------------------------- |
| `username`       | `string`   | `run`      | Guest OS username (`-u`) — **required**           |
| `password`       | `string`   | `run`      | Guest OS password (`-p`) — **required**           |
| `program`        | `string`   | `run`      | Absolute path to the program to execute — **required** |
| `program_args`   | `string[]` | `run`      | Program arguments, each as a separate string      |
| `activate_window`| `boolean`  | `run`      | Bring the guest window to the foreground (`-aw`)  |
| `no_wait`        | `boolean`  | `run`      | Return immediately after start (`-nw`)            |
| `interactive`    | `boolean`  | `run`      | Force interactive guest login (`-i`)              |
| `working_dir`    | `string`   | `run`      | Working directory in the guest (`-w`)             |
| `environment`    | `string[]` | `run`      | Environment variables to set (`-e`, one per entry)|

> **Note:** `vmcli Guest run` starts a program inside the guest but does not capture its stdout. To retrieve output, redirect to a file inside the guest and use `copyFrom` to retrieve it. Pass shell invocations as `program: "/bin/sh"` with `program_args: ["-c", "<shell command>"]`.

> **Note:** All other Guest actions (`query`, `copyFrom`, `copyTo`, `ps`, `ls`, …) use `command_args` as the escape hatch. VMware Tools must be running and the VM must be powered on.

**`vm_lifecycle`**

| Field              | Description              |
| ------------------ | ------------------------ |
| `custom_guesttype` | Custom guest type (`-c`) |
| `dirpath`          | VM directory (`-d`)      |
| `guesttype`        | Guest OS type (`-g`)     |
| `name`             | VM name (`-n`)           |

**`vm_power_management`**

| Field          | Applies To | Description                                       |
| -------------- | ---------- | ------------------------------------------------- |
| `paused`       | `Start`    | Start paused (`--paused`)                         |
| `soft`         | `Start`    | Soft start (`--soft`)                             |
| `stop_op_type` | `Stop`     | `trySoft`, `requireSoft`, `configDefault`, `hard` |

**`vm_snapshot_management`**

| Field            | Applies To | Description                |
| ---------------- | ---------- | -------------------------- |
| `description`    | `Take`     | `--description`            |
| `include_memory` | `Take`     | `--memory`                 |
| `snapshot_name`  | `Take`     | Snapshot name (positional) |

## Tool Results

- **Success:** text content with vmcli stdout (often JSON for `query` actions)
- **Failure:** `isError: true` with `VMware vmcli error: …` in text content
- **Validation errors** (missing `vmx_path`, invalid `action`): raised before vmcli runs

See [Error Handling](error-handling.md) for details.

## Manifest Drift

After a VMware desktop hypervisor upgrade, regenerate the checked-in manifest:

```bash
make discover
```

Commit `manifest.json`, `_generated_actions.py`, and `tests/fixtures/manifest_command_counts.json` when command counts change.
