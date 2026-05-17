"""NATS testcontainer fixtures."""

from __future__ import annotations

import time
from collections.abc import AsyncGenerator

import pytest


def _docker_available() -> bool:
    import shutil
    import subprocess

    if shutil.which("docker") is None:
        return False
    try:
        return (
            subprocess.run(
                ["docker", "info"], capture_output=True, timeout=5, check=False
            ).returncode
            == 0
        )
    except Exception:
        return False


@pytest.fixture(scope="session")
def nats_url() -> str:
    """Start a NATS 2.10-alpine container with JetStream enabled."""
    if not _docker_available():
        pytest.skip("Docker required")
    try:
        from testcontainers.core.container import DockerContainer
    except ImportError:
        pytest.skip("testcontainers not installed")

    container = DockerContainer("nats:2.10-alpine").with_exposed_ports(4222).with_command("-js")
    container.start()
    try:
        # Poll for the container being responsive on the published port,
        # which is more reliable across testcontainers versions than
        # wait_for_logs (whose signature is deprecation-shifting).
        host = container.get_container_host_ip()
        port = container.get_exposed_port(4222)
        # Give NATS a moment to bind + announce ready
        for _ in range(60):
            try:
                import socket as _socket

                s = _socket.create_connection((host, int(port)), timeout=0.5)
                s.close()
                break
            except OSError:
                time.sleep(0.5)
        # Final tiny settle
        time.sleep(0.5)
        yield f"nats://{host}:{port}"
    finally:
        container.stop()


@pytest.fixture
async def nats_provider(nats_url: str) -> AsyncGenerator:
    from hwhkit.config.base import Settings
    from hwhkit.core.context import AppContext
    from hwhkit.integrations.nats import NatsConfig, NatsProvider

    cfg = NatsConfig(servers=[nats_url])
    provider = NatsProvider(config=cfg)

    ctx = AppContext()
    ctx.config = Settings()
    await provider.setup(ctx)
    try:
        yield provider
    finally:
        await provider.shutdown()
