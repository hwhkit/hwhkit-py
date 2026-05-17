# Release checklist — 0.4.0-alpha.1 (and beyond)

This is the operational guide for cutting a release. Code-side everything
is in place; the actions below are **manual / external** — they touch
accounts, DNS, and GitHub settings.

---

## One-time setup (before the first release ever)

### 1. PyPI accounts

- [ ] Register the **`hwhkit` PyPI organization** at <https://pypi.org/manage/organizations/>.
  - Verify the org email.
  - Enable 2FA (TOTP or hardware key).
- [ ] Register the same org on **TestPyPI** (<https://test.pypi.org/manage/organizations/>).
- [ ] In both, configure **Trusted Publishing** for this repo:
  - Project name: `hwhkit`
  - Owner: `hwhkit` (GitHub org)
  - Repo: `hwhkit-py`
  - Workflow: `release.yml`
  - Environment: `pypi` (for PyPI), `testpypi` (for TestPyPI)

### 2. GitHub environment secrets / protection

In **Settings → Environments**, create two environments:

- `pypi` — required reviewers = you, deployment branches = `main` only.
- `testpypi` — same.

These don't need secrets (Trusted Publishing uses OIDC), but the
environment gates give you a manual approve step before each publish.

### 3. GitHub Pages (for docs.louishwh.tech subdomain)

- [ ] **Settings → Pages → Source: GitHub Actions** *(not branch)*.
- [ ] Add `hwhkit.louishwh.tech` as **Custom domain** and tick "Enforce HTTPS".
- [ ] DNS: add `CNAME hwhkit.louishwh.tech → hwhkit.github.io` (your DNS provider).

### 4. Branch protection (optional but recommended)

- **Settings → Branches → main**:
  - Require status checks to pass (CI lint + typecheck + test-unit + build + security).
  - Require linear history.
  - Allow force-push: disabled.

### 5. Apps to install on the `hwhkit` org

- [ ] **Renovate** — <https://github.com/apps/renovate> (config already in repo).
- [ ] (Optional) **Codecov** — <https://github.com/apps/codecov> for diff-coverage on PRs.

---

## Per-release procedure

### 1. Prepare

- [ ] All CI green on `main` (look at <https://github.com/hwhkit/hwhkit-py/actions>).
- [ ] CHANGELOG `[Unreleased]` section has entries; promote them under
      the new version heading with date.
- [ ] `hwhkit/__init__.py` `__version__` matches the tag you're about to cut.
- [ ] `pyproject.toml` `version = "..."` matches too.
- [ ] Run locally:
      ```bash
      make test          # 299 unit pass
      make lint          # ruff clean
      make typecheck     # mypy strict clean
      make docs          # mkdocs build --strict clean
      uv build           # produces dist/hwhkit-X.Y.Z.tar.gz + .whl
      ```

### 2. Tag & push

```bash
git tag v0.4.0a1 -m "0.4.0-alpha.1"
git push origin v0.4.0a1
```

The `release.yml` workflow fires automatically:

1. `build` — `uv build` → sdist + wheel
2. `sbom` — CycloneDX JSON of dependencies
3. `sign` — Sigstore attestation on each artifact
4. **For pre-release tags** (rc / alpha / beta): publish to **TestPyPI**
5. **For stable tags**: publish to **PyPI**
6. `github-release` — creates GitHub Release with auto-generated notes,
   dist files, and SBOM attached

### 3. Verify

- [ ] PyPI page shows the new version: <https://pypi.org/project/hwhkit/>
      (or TestPyPI: <https://test.pypi.org/project/hwhkit/>).
- [ ] GitHub Release page has all artifacts + Sigstore bundle.
- [ ] Sample install in a clean venv:
      ```bash
      uv pip install --index-url https://test.pypi.org/simple/ \
        --extra-index-url https://pypi.org/simple/ hwhkit==0.4.0a1
      python -c "import hwhkit; print(hwhkit.__version__)"
      ```

### 4. Docs deploy

The `docs.yml` workflow auto-publishes to GitHub Pages on every push to
`main` via `mike`. To version the docs explicitly for a release:

```bash
uv run mike deploy 0.4 latest --push
```

(After 1.0 we'll have `mike` deploy a `stable` alias too.)

---

## Rollback

If a release goes wrong:

1. **PyPI** — packages cannot be deleted, but you can **yank** them:
   <https://pypi.org/project/hwhkit/> → version → Yank.
2. **GitHub Release** — delete from the Releases UI; delete the tag locally
   and force-delete remotely:
   ```bash
   git tag -d v0.4.0a1
   git push origin :v0.4.0a1
   ```
3. Fix the bug, bump to the next pre-release (e.g. `v0.4.0a2`), re-cut.

---

## 0.4.0a1 → 1.0.0 path

| Version | What lands | Approx ETA |
|---|---|---|
| 0.4.0-alpha.1 | This release (foundation + P0/P1 integrations + CLI + docs) | Today |
| 0.4.0-beta.1 | Coverage to 85%+ ; benchmark baselines wired into CI ; chaos tests | +2 weeks |
| 0.4.0-rc.1 | API frozen; only bug fixes from here ; live on TestPyPI for soak | +3 weeks |
| 0.4.0 | First stable; PyPI publish | +4 weeks |
| 0.5.0–0.9.x | P2 adapter implementations (mysql / qdrant / mongodb / neo4j / s3 / oss) and lessons from production use; minor versions may carry breaking changes per the 0.x SemVer-relaxation note in docs/migration | +2-6 months |
| 1.0.0 | First strict-SemVer stable | when ready |

---

## Status at time of writing

- Repo: `github.com/hwhkit/hwhkit-py`
- Branch `main` HEAD: `fba83a9` (W6 docs complete)
- All quality gates green locally; CI status on `main` TBD until first push
  triggers it
- Wheel + sdist build cleanly via `uv build`
- Ready to tag `v0.4.0a1` once you've completed the one-time setup above
