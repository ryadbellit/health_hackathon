import socket

import pytest

from app.config import Settings
from app.network_guard import (
    OfflineModeBlockedError,
    install_network_guard,
    is_host_allowed,
    uninstall_network_guard,
)


@pytest.fixture(autouse=True)
def _restore_guard():
    yield
    uninstall_network_guard()


@pytest.fixture
def settings():
    return Settings(OFFLINE_MODE=True)


def test_loopback_hosts_allowed(settings):
    assert is_host_allowed("127.0.0.1", settings)
    assert is_host_allowed("localhost", settings)
    assert is_host_allowed("::1", settings)


def test_external_hosts_blocked(settings):
    assert not is_host_allowed("1.2.3.4", settings)
    assert not is_host_allowed("api.openai.com", settings)


def test_install_network_guard_blocks_external_connection(settings):
    install_network_guard(settings)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(OfflineModeBlockedError):
            sock.connect(("1.2.3.4", 80))
    finally:
        sock.close()


def test_disabled_offline_mode_skips_guard():
    settings = Settings(OFFLINE_MODE=False)
    install_network_guard(settings)
    # No guard installed, no error raised here - this just documents the no-op.
