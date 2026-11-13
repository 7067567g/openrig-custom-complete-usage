# Rendered OpenRig bundle

A real run places these generated files here:

```text
openrig/rig.yaml
openrig/workflow.yaml
openrig/agents/worker/agent.yaml
openrig/guidance/team.md
openrig/OPENRIG-BRIDGE.json
```

Generate them with:

```bash
python3 templates/specialized/openrig-workflow-master/render_master.py \
  --run-id demo-run \
  --project-root "<target-repo>" \
  --output-dir examples/sanitized-run/openrig
```
