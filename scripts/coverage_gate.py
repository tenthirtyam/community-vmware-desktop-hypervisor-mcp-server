# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

#!/usr/bin/env python3
"""Enforce per-module coverage thresholds from coverage.xml."""

from __future__ import annotations

import sys
from pathlib import Path

from defusedxml import ElementTree

THRESHOLDS: dict[str, int] = {
    "handlers.py": 85,
    "discovery.py": 85,
    "schemas.py": 85,
    "vmcli.py": 85,
    "manifest.py": 85,
    "inventory.py": 85,
    "platform_detector.py": 85,
    "server_common.py": 85,
}

COVERAGE_XML = Path(__file__).resolve().parents[1] / "coverage.xml"


def _write_error(message: str) -> None:
    """Write a single error line to stderr."""
    sys.stderr.write(f"{message}\n")


def _write_status(message: str) -> None:
    """Write a single status line to stdout."""
    sys.stdout.write(f"{message}\n")


def main() -> int:
    """Validate per-module coverage thresholds from coverage.xml."""
    if not COVERAGE_XML.is_file():
        _write_error(f"coverage.xml not found at {COVERAGE_XML}")
        return 1

    root = ElementTree.parse(COVERAGE_XML).getroot()
    if root is None:
        _write_error("coverage.xml has no root element")
        return 1
    failures: list[str] = []
    for cls in root.findall(".//class"):
        filename = cls.get("filename", "")
        for suffix, minimum in THRESHOLDS.items():
            if not filename.endswith(suffix):
                continue
            line_rate = float(cls.get("line-rate", "0"))
            pct = round(line_rate * 100, 1)
            if pct < minimum:
                failures.append(f"{filename}: {pct}% < {minimum}%")
            break

    missing = set(THRESHOLDS) - {
        suffix
        for suffix in THRESHOLDS
        if any((cls.get("filename") or "").endswith(suffix) for cls in root.findall(".//class"))
    }
    for suffix in sorted(missing):
        failures.append(f"No coverage data for *{suffix}")

    if failures:
        _write_error("Coverage gate failed:")
        for msg in failures:
            _write_error(f"  - {msg}")
        return 1

    _write_status("Coverage gate passed for all core modules.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
