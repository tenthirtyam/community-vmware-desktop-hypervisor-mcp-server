# Development

A guide for collaborators.

## Quick Start

```bash
make venv
make install-dev
make check
```

## Common Commands

| Command                                       | Purpose                                              |
| --------------------------------------------- | ---------------------------------------------------- |
| `make check`                                  | Run `ruff` + `mypy` + unit tests + coverage gate.    |
| `make test`                                   | Run unit local tests.                                |
| `make test-e2e`                               | Run tests on VMware (`VMCLI_E2E=1`)                    |
| `make discover`                               | Regenerate `manifest.json` + `_generated_actions.py`.|
| `make install-docs && make docs-serve`        | Build and preview the documentation.                 |
| `make install-cursor` / `make install-vscode` | Verify the MCP host configuration.                    |

## Development Container

This repository includes [`.devcontainer/devcontainer.json`](../.devcontainer/devcontainer.json) for
a lightweight collaborator setup in VS Code or GitHub Codespaces.

- Supports documentation, linting, typechecking, mocked unit tests, and general package development.
- Runs `make install-dev && make install-docs` after the container is created.
- Forwards port `8000` for `make docs-serve`.
- Does not include VMware Fusion, VMware Workstation, or `vmcli`.

Use the host machine, not the develoment container, for live workflows such as `make test-e2e`,
`make test-e2e-capabilities`, or manual `vmcli` verification.

## Unit Testing

```bash
pytest                          # Run all unit tests.
pytest tests/test_vmcli.py -v   # Run all units tests from a single file.
make test-cov                   # Run all unit test with a coverage report.
```

Coverage gate (≥85%) applies to core modules: `handlers`, `discovery`, `schemas`, `vmcli`,
`manifest`, `inventory`, `platform_detector`, `server_common`.

## End-to-End Testing

Requires VMware Fusion on macOS:

| Variable           | Purpose                                     |
| ------------------ | ------------------------------------------- |
| `VMCLI_E2E`          | Set to `1` to run tests on a VMware Fusion. |
| `VMCLI_E2E_VMX_PATH` | Absolute path to a test `.vmx` file.         |

```bash
export VMCLI_E2E=1
export VMCLI_E2E_VMX_PATH=/path/to/vm.vmx
make test-e2e
make test-e2e-capabilities
```

## Documentation Site

```bash
make install-docs
make docs-serve     # http://127.0.0.1:8000
```

Built with [Properdocs](https://pypi.org/project/properdocs/) and
[MaterialX](https://github.com/jaywhj/mkdocs-materialx).

## Release

1. Bump `version` in `pyproject.toml` and `server.json`, keeping them in sync.
2. Commit and push to `main`.
3. Tag and push: `git tag v0.1.0 && git push origin v0.1.0`

The release workflow]builds the package, created the release, and publishes to
[PyPI](https://pypi.org/project/community-vmware-desktop-hypervisor-mcp-server/).

## Pull Request Checklist

1. Ensure `make check` passes locally.
2. If the `vmcli` surface changes, run `make discover` and commit manifest artifacts.
