
.PHONY: data build_runner train eval report smoke

# Placeholder targets for Phase 1 scaffold

data:
        @echo "Data pipeline not implemented yet"

build_runner:
        docker build -f runner.Dockerfile -t hrm-runner .

train:
        python -m hrm_coder.train $(ARGS)

eval:
        python -m hrm_coder.eval_cli $(ARGS)

report:
        @echo "Report generation not implemented yet"

smoke:
        python scripts/smoke_train.py
