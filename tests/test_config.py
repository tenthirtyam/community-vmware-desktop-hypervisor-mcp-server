# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Tests for environment configuration."""

from __future__ import annotations

from unittest.mock import patch

from community_vmware_desktop_hypervisor_mcp_server.config import Settings, get_settings


def test_vm_search_paths() -> None:
    with patch.dict("os.environ", {"VMCLI_SEARCH_PATHS": "/a:/b"}, clear=False):
        settings = Settings.from_env()
    assert settings.vm_search_paths == ("/a", "/b")


def test_from_env_invalid_values_fall_back() -> None:
    with patch.dict(
        "os.environ",
        {
            "VMCLI_OUTPUT_FORMAT": "xml",
            "VMCLI_TIMEOUT_SECONDS": "not-a-number",
            "VMCLI_LOG_LEVEL": "info",
        },
        clear=True,
    ):
        settings = Settings.from_env()

    assert settings.vmcli_output_format == "json"
    assert settings.vmcli_format_flag == "json"
    assert settings.vmcli_timeout_seconds == 120.0
    assert settings.log_level == "INFO"


def test_get_settings_caches_result() -> None:
    with patch("community_vmware_desktop_hypervisor_mcp_server.config._settings", None):
        first = get_settings()
        second = get_settings()

    assert first is second
