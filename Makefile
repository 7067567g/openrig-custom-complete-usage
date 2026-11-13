.RECIPEPREFIX = >
PY ?= python3
PYTEST ?= $(PY) -m pytest

.PHONY: check test doc demo render-dry smoke bench-smoke clean

check:
> $(PY) scripts/check_repo.py
> $(PY) scripts/check_content.py
> $(PY) scripts/check_sanitization.py
> $(PY) -m compileall -q scripts sctg-kit tests tools/lead-guide

test: check
> $(PY) tools/lead-guide/tests/test_lead_guide.py
> $(PYTEST) tests -q

demo:
> $(PY) examples/sctg-minimal/run_demo.py
> $(PY) examples/multi-card/run_demo.py
> $(PY) examples/decision/run_demo.py
> $(PY) examples/rollback/run_demo.py
> $(PY) examples/two-seat-handoff/run_demo.py

doc:
> $(PY) scripts/doc_consistency.py --check

render-dry:
> mkdir -p /tmp/openrig-demo-project
> $(PY) templates/specialized/openrig-workflow-master/render_master.py \
>   --run-id demo-001 \
>   --project-root /tmp/openrig-demo-project \
>   --output-dir /tmp/openrig-demo-render \
>   --dry-run --json

smoke:
> $(PY) scripts/openrig_smoke.py --rounds 3

bench-smoke:
> @echo "BENCHMARK NOT RUN: budget unavailable; see process/BENCHMARK-STATUS.md"
> @echo "The real harness is benchmark/harness/run_benchmark.py; do not run it without an explicit budget."
> @exit 0

clean:
> find . -type d -name '__pycache__' -prune -exec rm -rf {} +
> find . -name '*.pyc' -delete
> rm -rf .pytest_cache
