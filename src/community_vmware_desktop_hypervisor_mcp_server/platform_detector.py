# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Resolve the vmcli binary path and detect the hypervisor UI for the current platform."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path

DEFAULT_PATHS: dict[str, Path] = {
    "darwin": Path("/Applications/VMware Fusion.app/Contents/Public/vmcli"),
    "linux": Path("/usr/bin/vmcli"),
    "windows": Path(r"C:\Program Files (x86)\VMware\VMware Workstation\vmcli.exe"),
}

_UI_PROCESS_NAMES: dict[str, str] = {
    "darwin": "VMware Fusion",
    "linux": "vmware",
    "windows": "vmware.exe",
}

_UI_OPEN_EXECUTABLES: dict[str, list[str]] = {
    "darwin": [
        "/Applications/VMware Fusion.app/Contents/MacOS/VMware Fusion",
    ],
    "linux": ["/usr/bin/vmware"],
    "windows": [
        r"C:\Program Files (x86)\VMware\VMware Workstation\vmware.exe",
        r"C:\Program Files\VMware\VMware Workstation\vmware.exe",
    ],
}


def _platform_key() -> str:
    """Normalize platform.system() to the internal default-path key."""
    system = platform.system().casefold()
    if system.startswith("win"):
        return "windows"
    return system


def resolve_vmcli() -> Path:
    """Return path to vmcli, raising FileNotFoundError if not found."""
    override = os.environ.get("VMCLI_PATH")
    if override:
        path = Path(override).expanduser()
        if path.is_file():
            return path.resolve()
        msg = f"VMCLI_PATH not found: {override}"
        raise FileNotFoundError(msg)

    candidate = DEFAULT_PATHS.get(_platform_key())
    if candidate is not None and candidate.is_file():
        return candidate.resolve()

    found = shutil.which("vmcli")
    if found:
        return Path(found).resolve()

    msg = (
        "vmcli not found. Install VMware Fusion/Workstation or set VMCLI_PATH to the vmcli binary."
    )
    raise FileNotFoundError(msg)


def is_hypervisor_ui_running() -> bool:
    """Return True if the VMware Fusion or Workstation UI process is running."""
    key = _platform_key()
    process_name = _UI_PROCESS_NAMES.get(key, "vmware")
    try:
        if key == "windows":
            tasklist = shutil.which("tasklist") or "tasklist"
            out = subprocess.run(  # noqa: S603
                [tasklist, "/fi", f"imagename eq {process_name}", "/fo", "csv", "/nh"],
                capture_output=True,
                check=False,
                text=True,
                timeout=5,
            ).stdout
            return process_name.lower() in out.lower()
        pgrep = shutil.which("pgrep") or "pgrep"
        rc = subprocess.run(  # noqa: S603
            [pgrep, "-x", process_name], capture_output=True, check=False, timeout=5
        ).returncode
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False
    else:
        return rc == 0


def get_ui_open_args(vmx_path: Path) -> list[str] | None:
    """Return argv to open *vmx_path* in the hypervisor UI, or None if unavailable.

    - macOS:   ``open <bundle.vmwarevm>``
    - Windows: ``vmware.exe <vmx_path>``
    - Linux:   ``vmware <vmx_path>``
    """
    key = _platform_key()
    if key == "darwin":
        bundle = vmx_path.parent if vmx_path.suffix == ".vmx" else vmx_path
        return ["open", str(bundle)]
    for exe in _UI_OPEN_EXECUTABLES.get(key, []):
        if Path(exe).is_file():
            return [exe, str(vmx_path)]
    found = shutil.which("vmware")
    if found:
        return [found, str(vmx_path)]
    return None
