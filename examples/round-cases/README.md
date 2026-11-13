**English** | [简体中文](README.zh-CN.md)

# 12-round workflow cases

Three synthetic but real 12-round workflow-group cases. Each case was generated
by running the actual `wf.py new-run / append-status / state / new-round`
commands, then exported and sanitized.

| Case | Focus |
|---|---|
| [`case-12-rounds-hardening`](case-12-rounds-hardening/README.md) | harden a small service over 12 rounds |
| [`case-12-rounds-release`](case-12-rounds-release/README.md) | prepare a release over 12 rounds |
| [`case-12-rounds-docs`](case-12-rounds-docs/README.md) | improve bilingual docs over 12 rounds |

Each case contains 12 `STATUS-Round-N.md`, 12 decisions, `ROUNDS.md`,
`ROUNDS.json`, and evidence logs. They are illustrative, not real project data.
