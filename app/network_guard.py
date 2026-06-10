"""Runtime enforcement of OFFLINE_MODE.

When ``Settings.OFFLINE_MODE`` is true, ``install_network_guard()`` patches
``socket.socket.connect`` so that any attempt to reach a host outside of
``Settings.ALLOWED_HOSTS`` (loopback only by default) raises immediately,
before any bytes leave the machine. It also sets a handful of well-known
"offline" environment variables so libraries such as ``transformers`` /
``huggingface_hub`` don't attempt their own update/telemetry checks even if
imported.

This is the single chokepoint the app and the test suite both rely on - see
docs/wiki/Offline-Mode.md.
"""

from __future__ import annotations

import ipaddress
import os
import socket

from app.config import Settings

_original_connect = socket.socket.connect
_guard_installed = False

_OFFLINE_ENV_DEFAULTS = {
    "HF_HUB_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1",
    "HF_HUB_DISABLE_TELEMETRY": "1",
    "HF_HUB_DISABLE_IMPLICIT_TOKEN": "1",
}


class OfflineModeBlockedError(RuntimeError):
    """Raised when OFFLINE_MODE blocks an outbound network connection."""


def is_host_allowed(host: str | None, settings: Settings) -> bool:
    """Return True if ``host`` may be reached while OFFLINE_MODE is enabled."""
    if host is None:
        return True
    if host in settings.ALLOWED_HOSTS:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def install_network_guard(settings: Settings) -> None:
    """Apply the offline network guard if ``settings.OFFLINE_MODE`` is true.

    Safe to call multiple times - subsequent calls are no-ops once installed.
    """
    if not settings.OFFLINE_MODE:
        return

    for key, value in _OFFLINE_ENV_DEFAULTS.items():
        os.environ.setdefault(key, value)

    global _guard_installed
    if _guard_installed:
        return

    def guarded_connect(self: socket.socket, address):
        host = address[0] if isinstance(address, tuple) else address
        if not is_host_allowed(host, settings):
            raise OfflineModeBlockedError(
                f"OFFLINE_MODE is enabled: outbound connection to {host!r} is blocked"
            )
        return _original_connect(self, address)

    socket.socket.connect = guarded_connect
    _guard_installed = True


def uninstall_network_guard() -> None:
    """Restore the original ``socket.socket.connect`` (used by tests)."""
    global _guard_installed
    socket.socket.connect = _original_connect
    _guard_installed = False
