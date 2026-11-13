.RECIPEPREFIX = >
PY ?= python3
PYTEST ?= $(PY) -m pytest

.PHONY: check test doc render-dry smoke clean

check:
> $(PY) scripts/check_repo.py
> $(PY) -m compileall -q scripts sctg-kit tests

test: check
> $(PYTEST) tests -q

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

clean:
> find . -type d -name '__pycache__' -prune -exec rm -rf {} +
> find . -name '*.pyc' -delete
> rm -rf .pytest_cache
