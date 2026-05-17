# Migration guides

When hwhkit makes a breaking change, the entry to upgrade lives here.

## Current

- **0.4.x → 1.0.0** — *Coming soon.* 0.4 is the alpha series; 1.0
  consolidates the spec. The `hwhkit upgrade` CLI will ship with libcst
  codemods covering each breaking change so you can run them
  automatically.

## Deprecation policy

- Every API marked `@deprecated` lives for **at least one minor version**
  before removal in a major version.
- Deprecation emits a `DeprecationWarning` at import or first call.
- The CHANGELOG documents what was deprecated, when, and why.
- For every breaking change, `hwhkit upgrade` ships a codemod that rewrites
  user code automatically.

## SemVer for 0.x

While the version is `0.x.y`:

- **`x` may break things.** Each `0.x` bump may include breaking changes.
  Always read the release notes.
- **`y` is strictly non-breaking.** Patch versions only fix bugs.

From `1.0.0` onwards, strict SemVer: no breaking changes outside of
major bumps.
