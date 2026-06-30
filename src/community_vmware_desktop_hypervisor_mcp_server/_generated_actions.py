# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Auto-generated action Literals from vmcli discovery. Do not edit."""

from __future__ import annotations

from typing import Literal

ChipsetAction = Literal[
    "query", "SetCoresPerSocket", "SetMemSize", "SetSimultaneousThreads", "SetVCpuCount"
]

ConfigParamsAction = Literal["query", "SetEntry"]

DiskAction = Literal[
    "Branch",
    "BranchCancel",
    "ConnectionControl",
    "ConvertAllocType",
    "ConvertAllocTypeCancel",
    "Create",
    "Extend",
    "IsPresent",
    "Move",
    "Purge",
    "query",
    "SetAllowGuestControl",
    "SetBackingInfo",
    "SetBandwidthCap",
    "SetCbrcCacheEnabled",
    "SetCtkEnabled",
    "SetDigest",
    "SetDiskUUID",
    "SetDiskUuidEnabled",
    "SetExclusiveAccess",
    "SetGlobalCtkDisallowed",
    "SetHardDiskHostBuffer",
    "SetHardDiskPageAlign",
    "SetHideTypeOfROnlyPart",
    "SetMode",
    "SetPolicy",
    "SetPresent",
    "SetReadOnly",
    "SetReservation",
    "SetShares",
    "SetSharing",
    "SetSpifFilters",
    "SetStartConnected",
    "SetThroughputCap",
    "SetWriteThrough",
]

EthernetAction = Literal[
    "ConnectionControl",
    "IsPresent",
    "MoveDevice",
    "Purge",
    "query",
    "SetAddressType",
    "SetAllowGuestControl",
    "SetConnectionType",
    "SetCustomTypeBacking",
    "SetDvsTypeBacking",
    "SetExternalId",
    "SetFeatures",
    "SetLinkStatePropagation",
    "SetMigrateControl",
    "SetNetworkName",
    "SetNiocTypeBacking",
    "SetOpaqueNetworkTypeBacking",
    "SetPciSlotNumber",
    "SetPresent",
    "SetPvnTypeBacking",
    "SetSecurityPolicy",
    "SetStartConnected",
    "SetTransferLatency",
    "SetTransferRate",
    "SetUptCompatibility",
    "SetVirtualDevice",
    "SetWakeOnPcktRcv",
]

GuestAction = Literal[
    "copyFrom",
    "copyTo",
    "createTempDir",
    "createTempFile",
    "env",
    "kill",
    "ls",
    "mkdir",
    "mv",
    "mvdir",
    "ps",
    "query",
    "rm",
    "rmdir",
    "run",
    "toolsproperties",
]

HGFSAction = Literal[
    "query",
    "SetEnabled",
    "SetExpiration",
    "SetFollowSymlinks",
    "SetGuestName",
    "SetHostDefaultCase",
    "SetHostPath",
    "SetPresent",
    "SetReadAccess",
    "SetTags",
    "SetWriteAccess",
]

MKSAction = Literal[
    "captureScreenshot",
    "query",
    "sendKeyEvent",
    "sendKeySequence",
    "SetAccel3d",
    "SetFullscreenAtPowerOn",
    "SetFullScreenOnAllHostDisplays",
    "SetGraphicsMemoryKB",
    "SetGuestResolution",
    "SetNumDisplays",
    "SetRenderer3d",
    "SetVramSize",
]

NvmeAction = Literal[
    "FindFirstFree",
    "IsChildPresent",
    "Move",
    "Purge",
    "query",
    "SetBusType",
    "SetMaxDevices",
    "SetPciSlotNumber",
    "SetPresent",
    "SetType",
]

PowerAction = Literal["Pause", "query", "Reset", "Start", "Stop", "Suspend", "Unpause"]

SataAction = Literal[
    "FindFirstFree",
    "HasNoDevice",
    "IsChildPresent",
    "IsPresent",
    "Move",
    "Purge",
    "query",
    "SetMaxDevices",
    "SetNumaNode",
    "SetPciSlotNumber",
    "SetPresent",
    "SetType",
]

SerialAction = Literal[
    "ConnectionControl",
    "Purge",
    "Query",
    "SetAllowGuestControl",
    "SetBackingInfo",
    "SetPresent",
    "StartConnected",
    "TryNoRxLoss",
    "YieldOnMsrRead",
]

SnapshotAction = Literal["Clone", "Delete", "query", "Revert", "Take"]

ToolsAction = Literal["Install", "Query", "Upgrade"]

VMAction = Literal["Create"]

VMTemplateAction = Literal["Create", "Deploy"]

VProbesAction = Literal["Load", "Query", "Reset", "SetEnabled"]
