# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

"""Application context (shared VmCliRunner) via contextvars."""

from __future__ import annotations

import contextvars
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .vmcli import VmCliRunner

_app_context: contextvars.ContextVar[AppContext | None] = contextvars.ContextVar(
    "app_context",
    default=None,
)


@dataclass
class AppContext:
    """Runtime context initialized at server startup."""

    runner: VmCliRunner


def set_app_context(ctx: AppContext) -> contextvars.Token[AppContext | None]:
    """Set the current app context; returns token for reset."""
    return _app_context.set(ctx)


def reset_app_context(token: contextvars.Token[AppContext | None]) -> None:
    """Restore the previous app context."""
    _app_context.reset(token)


def get_app_context() -> AppContext:
    """Return the current app context, creating a default runner if unset."""
    ctx = _app_context.get()
    if ctx is None:
        from .vmcli import VmCliRunner

        return AppContext(runner=VmCliRunner())
    return ctx


def get_runner() -> VmCliRunner:
    """Return the shared vmcli runner from the current app context."""
    return get_app_context().runner
