.PHONY: data build_runner train eval report smoke cpp-build cpp-test

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

# Basic C++ build and test targets for Phase 1 scaffolding
CPP_PRESET ?= sanitized

cpp-build:
	cmake --preset $(CPP_PRESET) -S hrm_coder/cpp
	cmake --build build/$(CPP_PRESET)

cpp-test: cpp-build
	ctest --test-dir build/$(CPP_PRESET) --output-on-failure
