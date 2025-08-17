.PHONY: data build_runner build_trainer train eval report lint smoke cpp-build cpp-test test tooling

# Phase 1 scaffold targets
# Pass extra command line arguments to individual targets via the ARGS
# variable, for example:
#
#     make train ARGS='--seed 123'

DATA_OUT ?= data/processed

data:
	python scripts/build_data.py --output $(DATA_OUT) $(ARGS)

build_runner:
	docker build -f runner.Dockerfile -t hrm-runner .

build_trainer:
	docker build -f trainer.Dockerfile -t hrm-trainer .

train:
	python -m hrm_coder.train $(ARGS)

eval:
	python -m hrm_coder.eval_cli $(ARGS)

report:
	python scripts/report.py $(ARGS)

lint:
	pre-commit run --all-files

smoke:
	python scripts/smoke_train.py

# Run Python and C++ tests
test: cpp-test
	pytest $(ARGS)

# Convenience target aggregating lint and tests
tooling: lint test

# Basic C++ build and test targets for Phase 1 scaffolding
CPP_PRESET ?= sanitized

cpp-build:
	cmake --preset $(CPP_PRESET)
	cmake --build build/$(CPP_PRESET)

cpp-test: cpp-build
	ctest --test-dir build/$(CPP_PRESET) --output-on-failure
