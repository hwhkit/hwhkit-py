# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Greenfield rewrite of hwhkit-py, mirroring hwhkit-rs architecture.
- `hwhkit.core.contracts.*` protocols (Cache, MessageBus, RelationalDb, ...).
- `hwhkit.core.integration.IntegrationProvider` ABC.
- `hwhkit.core.errors` with 6-digit error code taxonomy.
- CI/CD pipeline (GitHub Actions).
- mkdocs-material documentation site at hwhkit.louishwh.tech.

### Removed
- Legacy `infoman` code (see commit history).

## [0.4.0-alpha.1] - TBD
- Alpha 1 of the rewrite. Foundation only — no integrations implemented yet.
