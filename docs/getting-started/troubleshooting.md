# Troubleshooting

Symptom → fix tables.

- For failure types and debugging flow, please refer to [Error Handling](error-handling.md).
- For host setup, please refer to [Integration](integration.md).

## MCP Host Cannot Start the Server

| Symptom                                | Fix                                                                 |
| -------------------------------------- | ------------------------------------------------------------------- |
| `vmcli not found` at startup           | Install Fusion/Workstation; set `VMCLI_PATH` in `env`               |
| `No such file or directory` for Python  | Use absolute paths; try `uv`; `make install-cursor` for development |
| `~` not expanded in workspace path     | Use shell wrapper from [Integration](integration.md)                |

## Tools Return Errors

| Symptom                          | Fix                                                              |
| -------------------------------- | ---------------------------------------------------------------- |
| `vm_list` returns `[]`           | Set `VMCLI_SEARCH_PATHS`: [Configuration](configuration.md)          |
| `Could not resolve vmx_path`     | Run `vm_list`; use `id`, `display_name`, or absolute `.vmx` path |
| `isError: true` on tool call     | Read message text: vmcli stderr is included                      |
| Guest operation fails            | Power on VM; guest must be running for many actions              |
| `Stop` fails without guest tools | Default is `trySoft`; use `stop_op_type: "hard"`                 |
| Invalid `action`                 | Match vmcli casing; call `vm_discover_capabilities`              |

## Development

| Symptom                       | Fix                                                                 |
| ----------------------------- | ------------------------------------------------------------------- |
| Manifest integrity test fails | `make discover`; commit `manifest.json` and `_generated_actions.py` |
| Coverage gate fails           | Add tests for the reported module under `tests/`                    |

### End-to-End Testing

```bash
export VMCLI_E2E=1
export VMCLI_E2E_VMX_PATH=/path/to/vm.vmx
make test-e2e
make test-e2e-capabilities
```
