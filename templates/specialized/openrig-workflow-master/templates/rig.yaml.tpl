version: "0.2"
name: {{RIG_NAME}}
summary: >
  Hybrid workflow master: workflow-group control plane + OpenRig execution
  plane. Generated from openrig-workflow-master for run {{RUN_ID}}.

pods:
  - id: control
    label: Control
    members:
      - id: main
        agent_ref: "local:./agents/worker"
        profile: default
        runtime: opencode
        role: main
        cwd: {{PROJECT_ROOT_YAML}}
        model: {{OPENCODE_MODEL_YAML}}
      - id: pmo
        agent_ref: "local:./agents/worker"
        profile: default
        runtime: opencode
        role: pmo
        cwd: {{PROJECT_ROOT_YAML}}
        model: {{OPENCODE_MODEL_YAML}}
    edges:
      - kind: delegates_to
        from: main
        to: pmo

  - id: exec
    label: Execution
    members:
      - id: tdo-oc
        agent_ref: "local:./agents/worker"
        profile: default
        runtime: opencode
        role: tdo
        cwd: {{PROJECT_ROOT_YAML}}
        model: {{OPENCODE_MODEL_YAML}}
      - id: tdo-dsh
        agent_ref: "local:./agents/worker"
        profile: default
        runtime: dsh
        role: tdo
        cwd: {{PROJECT_ROOT_YAML}}
    edges:
      - kind: collaborates_with
        from: tdo-oc
        to: tdo-dsh

  - id: assurance
    label: Assurance
    members:
      - id: qa
        agent_ref: "local:./agents/worker"
        profile: default
        runtime: opencode
        role: qa
        cwd: {{PROJECT_ROOT_YAML}}
        model: {{OPENCODE_MODEL_YAML}}
    edges: []

edges:
  - kind: delegates_to
    from: control.pmo
    to: exec.tdo-oc
  - kind: delegates_to
    from: control.pmo
    to: exec.tdo-dsh
  - kind: can_observe
    from: assurance.qa
    to: exec.tdo-oc
  - kind: can_observe
    from: assurance.qa
    to: exec.tdo-dsh

startup:
  files:
    - path: guidance/team.md
      delivery_hint: guidance_merge
      required: true
