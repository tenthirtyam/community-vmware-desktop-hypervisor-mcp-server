# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Environment-based configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass

from .server_common import (
    OUTPUT_FORMAT_ALIASES,
    OUTPUT_FORMAT_MAP,
)


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    log_level: str
    vmcli_output_format: str
    vmcli_format_flag: str
    vmcli_timeout_seconds: float
    vm_search_paths: tuple[str, ...]

    @classmethod
    def from_env(cls) -> Settings:
        """Build runtime settings from environment variables."""
        fmt = os.environ.get("VMCLI_OUTPUT_FORMAT", "json").lower()
        fmt = OUTPUT_FORMAT_ALIASES.get(fmt, fmt)
        if fmt not in OUTPUT_FORMAT_MAP:
            fmt = "json"
        paths_raw = os.environ.get("VMCLI_SEARCH_PATHS", "")
        search_paths = tuple(p for p in paths_raw.split(os.pathsep) if p.strip())
        timeout_raw = os.environ.get("VMCLI_TIMEOUT_SECONDS", "120")
        try:
            timeout = float(timeout_raw)
        except ValueError:
            timeout = 120.0
        return cls(
            log_level=os.environ.get("VMCLI_LOG_LEVEL", "WARNING").upper(),
            vmcli_output_format=fmt,
            vmcli_format_flag=OUTPUT_FORMAT_MAP[fmt],
            vmcli_timeout_seconds=timeout,
            vm_search_paths=search_paths,
        )


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return cached runtime settings."""
    global _settings
    current = _settings
    if current is None:
        current = Settings.from_env()
        _settings = current
    return current
