# OpenRig process archive

This directory is a **sanitized public archive** of how one OpenRig practice was
built: the workflows, round briefs, governance protocols, registries, traces, and
the lessons learned while using them.

It is not a product manual. Start with the main guide:

- [`../docs/OPENRIG-WORKFLOW-GUIDE.md`](../docs/OPENRIG-WORKFLOW-GUIDE.md)
- [`../docs/LLM-MISREAD-QUICKREF.md`](../docs/LLM-MISREAD-QUICKREF.md)

## Reading order

1. [`STORY.md`](STORY.md) — how the practice evolved, in narrative form.
2. [`DECISIONS.md`](DECISIONS.md) — the decisions that shaped it and why.
3. [`PITFALLS.md`](PITFALLS.md) — concrete mistakes, symptoms, and fixes.
4. [`BENCHMARK-STATUS.md`](BENCHMARK-STATUS.md) — why benchmark tests were not run.
5. [`governance/`](governance/) — the reusable protocols.
6. [`registries/`](registries/) — machine-readable round/thinking indexes.
7. [`rounds/`](rounds/) — sanitized round briefs, workflow specs, and reports.
8. [`traces/`](traces/) — real workflow trace and run-log examples.
9. [`case-studies/`](case-studies/) — longer design/evaluation write-ups.
10. [`reports/`](reports/) — share, upstream-evaluation, and analysis reports.
11. [`PROVENANCE.md`](PROVENANCE.md) — what was copied, what was redacted, and why.

Many `docs/...`, `reports/...`, and `tools/...` paths inside the archive refer to
the private source workspace and are intentionally unresolved in this repository.
Companion scripts and templates referenced by the protocols (for example
`tools/*.mjs` and the round/evaluation templates) are not shipped.
`INVENTORY.json` counts the copied payload only; the top-level reading documents
are additional.

## Sanitization boundary

Included: Markdown, JSON, YAML, and text records that describe process and
reasoning. Removed or redacted: absolute home paths, host names, device
identifiers, account/user identifiers, tokens, raw chat bodies, screenshots,
logs that contain private content, and machine-local credentials. Project/case
codenames are retained as non-personal labels. Placeholders such as
`<WORKSPACE>`, `<BRIDGE_REPO>`, `<OPENRIG_SRC>`, and `<REDACTED_TOKEN>` are
intentional.

The archive is a **traceable sanitized snapshot**, not a byte-for-byte copy of
private source files.
