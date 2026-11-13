**English** | [简体中文](LIMITATIONS.zh-CN.md)

# Limitations

- This repository is a **usage example**, not a production control plane.
- No live 5-seat E2E run is claimed by the default validation.
- `rig workflow validate` and `rig up --plan` validate specs, not model quality.
- Live runs need configured OpenCode/DSH seats and an isolated OpenRig home.
- SCTG gates check structure, scope, evidence, and reproducibility — not semantic
  correctness.
- Template/role contracts are versioned; mixing versions across repositories is
  unsupported unless listed in a release note.
