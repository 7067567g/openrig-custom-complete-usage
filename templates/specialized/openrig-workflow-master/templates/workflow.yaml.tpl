# Generated hybrid workflow master. One workflow instance per bounded round.
#
# v1.2 bounded-rework shape (DECISIONS D-006, option B):
#   - QA is split per branch: qa_opencode verifies only the OpenCode branch,
#     qa_dsh only the DSH branch. Each maps its `failed` exit back to the TDO
#     step that owns that branch, so a failed review re-enters the same branch
#     instead of dead-ending the round.
#   - qa_join depends on BOTH branch verdicts, so closeout cannot start while
#     either branch is still being reworked.
#   - Only shipped engine language is used: `next_hop.on` (branch keys are the
#     closed exit enum; targets are static step ids) and
#     `loop_guards.max_hops` (enforced by the projector on every advance).
#
# Hop budget: the base dependency walk is plan(1) → implement_*(1) →
# qa_*(1) → qa_join(1), i.e. 4 routing advances to create close_round. Each
# failed QA adds exactly two advances on that branch (the failed edge back to
# the TDO, then that TDO's handoff into its QA). max_hops: 10 covers the base
# graph plus one complete rework of BOTH branches (4 + 2 + 2 = 8), with two
# further single-branch advances of headroom; exhaustion is converted by the
# engine into an honest `max_hops_exceeded` failure, never an unbounded loop.
workflow:
  id: {{WORKFLOW_ID}}
  version: 1
  objective: >
    Move one bounded project packet through PMO planning, OpenCode and DSH
    execution branches, QA join, and MAIN closeout.
  target:
    rig: {{RIG_NAME}}
  entry:
    role: pmo
  exception_routing:
    orchestrator_role: main
  coordination_terminal_turn_rule: hot_potato
  roles:
    pmo:
      preferred_targets: [control-pmo@{{RIG_NAME_RAW}}]
    tdo_opencode:
      preferred_targets: [exec-tdo-oc@{{RIG_NAME_RAW}}]
    tdo_dsh:
      preferred_targets: [exec-tdo-dsh@{{RIG_NAME_RAW}}]
    qa:
      preferred_targets: [assurance-qa@{{RIG_NAME_RAW}}]
    main:
      preferred_targets: [control-main@{{RIG_NAME_RAW}}]
  steps:
    - id: plan
      actor_role: pmo
      objective: Split the round into bounded OpenCode and DSH packets with evidence requirements.
      allowed_exits: [handoff, waiting, failed]
    - id: implement_opencode
      actor_role: tdo_opencode
      depends_on: [plan]
      objective: Execute the OpenCode branch and record proof.
      allowed_exits: [handoff, waiting, failed]
    - id: implement_dsh
      actor_role: tdo_dsh
      depends_on: [plan]
      objective: Execute the DSH branch and record proof.
      allowed_exits: [handoff, waiting, failed]
    - id: qa_opencode
      actor_role: qa
      depends_on: [implement_opencode]
      objective: Verify only the OpenCode branch evidence; a failed verdict returns that branch to its TDO.
      allowed_exits: [handoff, waiting, failed]
      next_hop:
        on: { failed: implement_opencode }
    - id: qa_dsh
      actor_role: qa
      depends_on: [implement_dsh]
      objective: Verify only the DSH branch evidence; a failed verdict returns that branch to its TDO.
      allowed_exits: [handoff, waiting, failed]
      next_hop:
        on: { failed: implement_dsh }
    - id: qa_join
      actor_role: qa
      depends_on: [qa_opencode, qa_dsh]
      objective: Join both branch verdicts, compare cross-branch evidence, and report S1/S2 issues.
      allowed_exits: [handoff, waiting, failed]
    - id: close_round
      actor_role: main
      depends_on: [qa_join]
      objective: Review QA and close the round in the control-plane DECISIONS.
      allowed_exits: [done, failed]
  invariants:
    continuation_required: true
    preserve_lineage: true
    closure_required: true
    allowed_exits: [handoff, waiting, done, failed]
  loop_guards:
    max_hops: 10
    spawn_budget: 0
  closure:
    success: Round closed with both runtime branches and QA proof.
    degraded: Round stopped with a named blocker.
    failed: Round failed with evidence.
