"""Verify all P2 placeholder integrations expose the expected API surface."""

from __future__ import annotations

import pytest
from hwhkit.integrations.mongodb import MongoDBConfig, MongoDBProvider
from hwhkit.integrations.mysql import MySQLConfig, MySQLProvider
from hwhkit.integrations.neo4j import Neo4jConfig, Neo4jProvider
from hwhkit.integrations.oss import OssConfig, OssProvider
from hwhkit.integrations.qdrant import QdrantConfig, QdrantProvider
from hwhkit.integrations.s3 import S3Config, S3Provider

PROVIDERS = [
    (MySQLProvider, MySQLConfig, "mysql"),
    (QdrantProvider, QdrantConfig, "qdrant"),
    (MongoDBProvider, MongoDBConfig, "mongodb"),
    (Neo4jProvider, Neo4jConfig, "neo4j"),
    (S3Provider, S3Config, "s3"),
    (OssProvider, OssConfig, "oss"),
]


@pytest.mark.parametrize(("provider_cls", "config_cls", "name"), PROVIDERS)
def test_placeholder_metadata(provider_cls, config_cls, name) -> None:
    p = provider_cls()
    assert p.name == name
    assert p.config_schema is config_cls
    assert p.implements == []


@pytest.mark.asyncio
@pytest.mark.parametrize(("provider_cls", "_config_cls", "_name"), PROVIDERS)
async def test_setup_raises_not_implemented(provider_cls, _config_cls, _name) -> None:
    p = provider_cls()
    with pytest.raises(NotImplementedError, match="P2 placeholder"):
        await p.setup(ctx=None)  # type: ignore[arg-type]


@pytest.mark.asyncio
@pytest.mark.parametrize(("provider_cls", "_config_cls", "_name"), PROVIDERS)
async def test_health_check_is_unhealthy(provider_cls, _config_cls, _name) -> None:
    status = await provider_cls().health_check()
    assert status.healthy is False
    assert "placeholder" in status.message.lower()
