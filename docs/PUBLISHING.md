# Publishing policy

This repository is intentionally a **sanitized complete usage example**, not a
dump of internal run data.

## Included

- workflow contracts, roles, templates, scripts;
- OpenRig render/preflight/bridge tooling;
- minimal and multi-round examples;
- tests and docs.

## Excluded

- real `runs/` data and transcripts;
- API keys, tokens, cookies, `.dsh` credentials;
- personal absolute paths;
- internal dashboards, monitor target files, systemd unit names;
- internal project names and snapshots;
- benchmark task statements that are not redistributable.

## Before publishing

```bash
grep -RIn --exclude-dir=.git -E '/home/|DEEPSEEK_API_KEY|sk-[A-Za-z0-9]' .
python3 scripts/doc_consistency.py --check
make test
```
