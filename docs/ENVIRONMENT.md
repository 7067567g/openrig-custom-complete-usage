# Environment

## Required for local-only mode

- Python 3.11+
- `pip install -r requirements-dev.txt`
- Git

## Required for hybrid OpenRig mode

- Node.js 24
- OpenRig CLI (`rig`)
- OpenCode and/or DSH seats configured
- An isolated `OPENRIG_HOME` and daemon port per run

## Optional

- `bwrap` / containers for benchmark sandboxing
- `gh` CLI for release automation

## Smoke

```bash
make check
make doc
make test
make render-dry
```

`make smoke` requires `rig` and renders three temporary bundles.
