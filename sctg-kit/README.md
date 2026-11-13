# Reference kit

This is a small reference implementation of the SCTG transaction mechanics:

- `sctg.py`: render/start/dispatch/collect/gate/report/metrics;
- `gates/`: deterministic schema, scope, evidence, and command gates;
- `decision.py`: decision request/record/replay helper;
- `ledger.py`: append-only ledger helper;
- `schemas/`: submission plus GateResult, Decision, Ledger, Handoff, Join schemas.

It intentionally does not include an OpenRig adapter, a workflow engine, or a
production scheduler. Those belong to the execution plane or to a separate
adapter project.

Dependencies: see [`../requirements.txt`](../requirements.txt).
