# Versioning

## Scheme

Semantic versioning: `MAJOR.MINOR.PATCH`.

- `MAJOR` — incompatible workflow/contract changes.
- `MINOR` — new templates, examples, adapters, or non-breaking tooling.
- `PATCH` — docs, fixes, tests, compatibility updates.

Current version: `0.1.0`.

## Release checklist

1. `make check`
2. `make doc`
3. `make test`
4. `make render-dry`
5. `python3 scripts/openrig_smoke.py --rounds 12` (requires `rig`)
6. Update `CHANGELOG.md` and `docs/releases/<version>.md`
7. Bump `VERSION` and `pyproject.toml` together
8. Commit, tag `v<version>`, push tag
9. Create GitHub release from the tag

## Two-repository compatibility

| Repository | Role |
|---|---|
| `SCTG-public` | stable reference kit |
| `openrig-personnal-use-and-workflow` | complete operational usage |

The kit version and this usage version are intentionally independent. Record the
tested pair in the release notes.
