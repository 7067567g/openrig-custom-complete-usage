# OpenRig minimal example

This example renders one hybrid bundle and shows how to validate the bridge.
It does not contain secrets or a live rig.

```bash
mkdir -p examples/openrig-minimal/project
python3 templates/specialized/openrig-workflow-master/render_master.py \
  --run-id openrig-minimal \
  --project-root "$PWD/examples/openrig-minimal/project" \
  --output-dir "$PWD/examples/openrig-minimal/openrig" \
  --opencode-model deepseek/deepseek-flash \
  --dsh-profile headless

python3 templates/specialized/openrig-workflow-master/tools/openrig_bridge.py doctor \
  --run-dir "$PWD/examples/openrig-minimal"
```

Expected:

```text
PASS bridge runId=openrig-minimal rig=openrig-openrig-minimal ...
seat map:
  main         control-main@openrig-openrig-minimal
  ...
```

To launch, follow `docs/OPENRIG.md`. A live launch requires the `rig` CLI and
configured OpenCode/DSH seats.
