**English** | [简体中文](README.zh-CN.md)

# Sanitized run sample

A small, synthetic control-plane sample. It shows the shape of a real run
without containing any project data, credentials, absolute paths, or
transcripts.

```text
examples/sanitized-run/
  PROJECT.md            goal / scope / metrics / round summary
  SPEC.md               run-specific rules
  DECISIONS.md          MAIN decisions
  STATUS-Round-1.md     TDO progress + evidence pointers
  ISSUES.md             QA findings
  openrig/README.md     where the rendered bundle goes
  sctg/submission.json  example submission
  sctg/gate-result.json example gate result
  evidence/README.md    evidence pointer convention
```

This sample is illustrative, not a replay of a real project.
