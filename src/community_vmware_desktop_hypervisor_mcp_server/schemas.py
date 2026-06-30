# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Pydantic models for MCP tool inputs."""

from __future__ import annotations

from typing import ClassVar, Literal, Self

from pydantic import BaseModel, Field, model_validator

from ._generated_actions import (
    ChipsetAction,
    ConfigParamsAction,
    DiskAction,
    EthernetAction,
    GuestAction,
    HGFSAction,
    MKSAction,
    NvmeAction,
    PowerAction,
    SataAction,
    SerialAction,
    SnapshotAction,
    ToolsAction,
    VMTemplateAction,
    VProbesAction,
)
from .manifest import action_requires_vmx
from .server_common import VmxPosition

OutputFormat = Literal["json", "yaml", "toml"]


class ModuleInvokeParams(BaseModel):
    """Common parameters for module-grouped vmcli tools."""

    action: str = Field(description="vmcli subcommand (exact casing)")
    vmx_path: str | None = Field(
        default=None,
        description="Absolute .vmx path, or inventory id/display_name from vm_list",
    )
    command_args: list[str] = Field(
        default_factory=list,
        description="Additional flags and positionals passed to vmcli",
    )
    vmx_position: VmxPosition = Field(
        default="first",
        description="Place vmx path first or last on the command line",
    )
    verbose: bool = Field(default=False, description="Pass --verbose to vmcli")
    output_format: OutputFormat | None = Field(
        default=None,
        description="For query/Query actions: -f format (json, yaml, or toml)",
    )


class VmxValidatedParams(ModuleInvokeParams):
    """Base for module tools that may require vmx_path."""

    module_name: ClassVar[str]

    @model_validator(mode="after")
    def validate_vmx_required(self) -> Self:
        """Ensure vmx_path is present when the selected action requires it."""
        action = str(self.action)
        if action_requires_vmx(self.module_name, action):
            if not self.vmx_path:
                msg = f"vmx_path is required for {self.module_name} {action}"
                raise ValueError(msg)
        return self


class ChipsetParams(VmxValidatedParams):
    module_name: ClassVar[str] = "Chipset"
    action: ChipsetAction


class ConfigParamsParams(VmxValidatedParams):
    module_name: ClassVar[str] = "ConfigParams"
    action: ConfigParamsAction


class DiskParams(VmxValidatedParams):
    module_name: ClassVar[str] = "Disk"
    action: DiskAction


class EthernetParams(VmxValidatedParams):
    module_name: ClassVar[str] = "Ethernet"
    action: EthernetAction


class GuestParams(VmxValidatedParams):
    module_name: ClassVar[str] = "Guest"
    action: GuestAction
    # run-action typed fields (ignored for all other actions)
    username: str | None = Field(default=None, description="run: guest username (-u)")
    password: str | None = Field(default=None, description="run: guest password (-p)")
    program: str | None = Field(default=None, description="run: path to the program to execute")
    program_args: list[str] = Field(
        default_factory=list,
        description="run: program arguments, each as a separate string",
    )
    activate_window: bool = Field(default=False, description="run: -aw/--activateWindow")
    no_wait: bool = Field(default=False, description="run: -nw/--noWait, return immediately")
    interactive: bool = Field(default=False, description="run: -i/--interactive guest login")
    working_dir: str | None = Field(default=None, description="run: -w/--workingDir")
    environment: list[str] = Field(
        default_factory=list,
        description="run: -e environment variable(s)",
    )

    @model_validator(mode="after")
    def validate_run_required_fields(self) -> Self:
        """Ensure username, password, and program are present for Guest run."""
        if str(self.action) == "run":
            if not self.username:
                msg = "username is required for Guest run"
                raise ValueError(msg)
            if not self.password:
                msg = "password is required for Guest run"
                raise ValueError(msg)
            if not self.program:
                msg = "program is required for Guest run"
                raise ValueError(msg)
        return self


class HGFSParams(VmxValidatedParams):
    module_name: ClassVar[str] = "HGFS"
    action: HGFSAction


class MKSParams(VmxValidatedParams):
    module_name: ClassVar[str] = "MKS"
    action: MKSAction


class NvmeParams(VmxValidatedParams):
    module_name: ClassVar[str] = "Nvme"
    action: NvmeAction


class SataParams(VmxValidatedParams):
    module_name: ClassVar[str] = "Sata"
    action: SataAction


class SerialParams(VmxValidatedParams):
    module_name: ClassVar[str] = "Serial"
    action: SerialAction


class ToolsParams(VmxValidatedParams):
    module_name: ClassVar[str] = "Tools"
    action: ToolsAction


class VMTemplateParams(VmxValidatedParams):
    module_name: ClassVar[str] = "VMTemplate"
    action: VMTemplateAction


class VProbesParams(VmxValidatedParams):
    module_name: ClassVar[str] = "VProbes"
    action: VProbesAction


PowerOffOpType = Literal["trySoft", "requireSoft", "configDefault", "hard"]


class PowerParams(VmxValidatedParams):
    module_name: ClassVar[str] = "Power"
    action: PowerAction
    paused: bool = Field(default=False, description="Start: -p/--paused")
    soft: bool = Field(default=False, description="Start: -s/--soft")
    stop_op_type: PowerOffOpType = Field(
        default="trySoft",
        description="Stop: -o/--opType when not set in command_args",
    )


class SnapshotParams(VmxValidatedParams):
    module_name: ClassVar[str] = "Snapshot"
    action: SnapshotAction
    snapshot_name: str | None = Field(default=None, description="Take: snapshot name positional")
    description: str | None = Field(default=None, description="Take: -d/--description")
    include_memory: bool = Field(default=False, description="Take: -m/--memory")


class VmCreateParams(BaseModel):
    action: Literal["Create"] = "Create"
    name: str = Field(description="VM name (-n)")
    dirpath: str = Field(description="Directory for VM files (-d)")
    guesttype: str | None = Field(default=None, description="Guest OS type (-g)")
    custom_guesttype: str | None = Field(default=None, description="Custom guest type (-c)")
    verbose: bool = False


MODULE_PARAM_TYPES: dict[str, type[VmxValidatedParams]] = {
    "Chipset": ChipsetParams,
    "ConfigParams": ConfigParamsParams,
    "Disk": DiskParams,
    "Ethernet": EthernetParams,
    "HGFS": HGFSParams,
    "MKS": MKSParams,
    "Nvme": NvmeParams,
    "Sata": SataParams,
    "Serial": SerialParams,
    "Tools": ToolsParams,
    "VMTemplate": VMTemplateParams,
    "VProbes": VProbesParams,
}

MODULE_TOOL_NAMES: dict[str, str] = {
    "Chipset": "vm_chipset_operations",
    "ConfigParams": "vm_config_params",
    "Disk": "vm_disk_operations",
    "Ethernet": "vm_ethernet_operations",
    "HGFS": "vm_hgfs_operations",
    "MKS": "vm_mks_operations",
    "Nvme": "vm_nvme_operations",
    "Sata": "vm_sata_operations",
    "Serial": "vm_serial_operations",
    "Tools": "vm_tools_management",
    "VMTemplate": "vm_template_management",
    "VProbes": "vm_vprobes_operations",
}


def _has_flag(args: list[str], *names: str) -> bool:
    """Return whether any of the provided flags already exists in args."""
    return any(arg in names for arg in args)


def build_power_extra_args(params: PowerParams) -> list[str]:
    """Build derived vmcli flags for Power actions."""
    extra: list[str] = list(params.command_args)
    if params.action == "Start":
        if params.paused:
            extra.append("--paused")
        if params.soft:
            extra.append("--soft")
    elif params.action == "Stop" and not _has_flag(extra, "-o", "--opType"):
        extra.extend(["-o", params.stop_op_type])
    return extra


def build_snapshot_extra_args(params: SnapshotParams) -> list[str]:
    """Build derived vmcli flags for Snapshot actions."""
    extra: list[str] = list(params.command_args)
    if params.action == "Take":
        if params.include_memory:
            extra.append("--memory")
        if params.description:
            extra.extend(["--description", params.description])
        if params.snapshot_name:
            extra.append(params.snapshot_name)
    return extra


def build_guest_extra_args(params: GuestParams) -> list[str]:
    """Build derived vmcli flags for Guest actions.

    For the ``run`` action the typed convenience fields are assembled into
    the correct argv.  All other actions fall back to ``command_args``.
    """
    if str(params.action) != "run":
        return list(params.command_args)
    args: list[str] = ["-u", params.username, "-p", params.password]  # type: ignore[list-item]
    if params.activate_window:
        args.append("--activateWindow")
    if params.no_wait:
        args.append("--noWait")
    if params.interactive:
        args.append("--interactive")
    if params.working_dir:
        args.extend(["-w", params.working_dir])
    for env_var in params.environment:
        args.extend(["-e", env_var])
    args.append(params.program)  # type: ignore[arg-type]
    args.extend(params.program_args)
    return args


def build_vm_create_args(params: VmCreateParams) -> list[str]:
    """Build vmcli arguments for creating a new virtual machine."""
    args = ["-n", params.name, "-d", params.dirpath]
    if params.guesttype:
        args.extend(["-g", params.guesttype])
    if params.custom_guesttype:
        args.extend(["-c", params.custom_guesttype])
    return args
