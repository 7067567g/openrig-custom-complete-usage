PY ?= python3
PYTEST ?= $(PY) -m pytest

.PHONY: test check render-dry preflight

test:
$(PYTEST) tests -q

check:
$(PY) scripts/doc_consistency.py --check

render-dry:
mkdir -p /tmp/openrig-demo-project
$(PY) templates/specialized/openrig-workflow-master/render_master.py \
  --run-id demo-001 \
  --project-root /tmp/openrig-demo-project \
  --output-dir /tmp/openrig-demo-render \
  --dry-run --json

preflight:
$(PY) scripts/openrig_preflight.py --json --no-monitor
