**English** | [简体中文](CONCEPTS.zh-CN.md)

# Concepts (local glossary)

This is a one-page vocabulary for readers starting from this repository. Deep
reference material is maintained in `SCTG-public` at tag `v0.5.1`.

| Term | Meaning here |
|---|---|
| **Card** | A bounded task with inputs, write scope, deliverable, and gates. |
| **Rig** | A live team topology: pods, seats, edges. |
| **Seat** | One agent identity in a rig; one active card at a time. |
| **Qitem / packet** | One queue item delivered to a seat. |
| **Workflow instance** | One run of a workflow spec; has a frontier and step trail. |
| **Step** | One declared unit in a workflow spec; not the same as a round. |
| **Closure** | The seat reports a packet outcome (`done`, `failed`, `handoff`, ...). |
| **Submission** | The producer's structured result: summary, changed files, commands, evidence. |
| **Gate** | Deterministic structural check: schema, scope, evidence, command. |
| **Decision** | An independent approval/replay record for an irreversible move. |
| **Ledger** | Append-only event history; not a chat transcript. |
| **Round** | One PMO -> TDO -> QA -> MAIN cycle in workflow-group. |
| **Bridge** | `OPENRIG-BRIDGE.json` mapping control-plane facts to execution-plane state. |
| **Control plane** | workflow-group documents: PROJECT, SPEC, DECISIONS, STATUS, ISSUES. |
| **Execution plane** | OpenRig: rig, seats, queue, workflow, transcripts, snapshots. |

Pinned reference: [`SCTG-public@v0.5.1`](https://github.com/7067567g/SCTG-public/tree/v0.5.1).
