[English](README.md) | **简体中文**

# OpenRig 最小示例

这个示例渲染一个 hybrid bundle，并检查 bridge。它不包含密钥，也不启动 live rig。

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

预期：

```text
PASS bridge runId=openrig-minimal rig=openrig-openrig-minimal ...
seat map:
  main         control-main@openrig-openrig-minimal
  ...
```

真实启动见 `docs/OPENRIG.zh-CN.md`，需要 `rig` CLI 和配置好的 OpenCode/DSH seat。
