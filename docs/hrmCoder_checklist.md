Project: HRM Coder

As development progresses each task is tracked using the symbols:

* `[ ]` not started
* `[~]` in progress
* `[?]` awaiting final review
* `[X]` complete

Save new code files in: C:\repos\hrm-coder

# Progress Checklist

** [~] Phase 0: Discovery & Reuse Audit
    [X] Inventory HRM repo APIs and identify injection points for C++ token/AST decoders
    [~] Setup project operation within isolate/gVisor runner images
    [~] Evaluate isolate and gVisor adapters against nsjail for reuse and gaps
        - Added sandbox detection utility for isolate, nsjail, and gVisor runsc runtime
    [~] Compile dataset catalog (Codeforces-Intro, AtCoder ABC subset, Kattis micro-set, HumanEval-CPP port) with licenses and hashes (see docs/dataset_catalog.json)
    [ ] Define acceptance metrics and thresholds for C++ (pass\@k, sanitizer-clean runs, timeout rate)
    [ ] Draft sandbox Threat Model and initial security requirements for native binaries
    [ ] Write ADRs for sandbox choice, experiment tracker, and GUI stack
    [ ] Create initial risk register and mitigation plan

** [ ] Phase 1: Repo Scaffold & Deterministic Environment
    [X] Generate project layout scaffold script for hrm-coder directory tree
    [?] Author runner.Dockerfile with g++, CMake, GoogleTest, isolate/nsjail, and sanitizer toolchain
    [~] Author trainer.Dockerfile with CUDA, PyTorch, and deterministic flags
    [~] Create Makefile targets for data, train, eval, and report (CMake + ctest integration)
    [~] Define Hydra config schema and default configs under conf/
    [?] Configure pre-commit for C++ (clang-format, clang-tidy, cpplint, codespell) and Python aux tools
    [X] Implement environment pinning and seed/tz/locale normalization module

** [~] Phase 2: GUI Stub and Backend Skeleton
    [X] Scaffold FastAPI app with /runs, /train, /eval, /logs/ws endpoints
    [X] Implement mock run registry with in-memory store and pagination
    [X] Build Run Console page with config pickers and action buttons
    [X] Build Jobs list page with sortable metrics and artifact links
    [X] Implement artifact static server for JUnit XML and lcov/llvm-cov HTML
    [X] Add WebSocket log streamer with tail-follow behavior
    [X] Provide GUI quickstart docs and sample configs

** [ ] Phase 3: Deterministic Dataset Pipeline (C++)
    [~] Implement HumanEval-CPP builder with harness generator and reference solutions
    [~] Implement Codeforces-Intro builder (I/O testcases, constraints, per-problem time limits)
    [~] Implement AtCoder ABC subset builder with normalized input/output cases
    [X] Write determinism validator to re-run and hash equality of artifacts
    [ ] Integrate DVC pipelines and data/versions.yml locking
    [~] Add dataset schema contracts and unit tests for loaders
    [~] Implement dataset split manager for train/val/test with fixed seeds

** [ ] Phase 4: Sandbox Executor
    [~] Implement isolate/nsjail adapter with CPU, RAM, wall time, and net-off policies
    [~] Implement C++ build-and-run pipeline (CMake/g++/clang++) with JUnit XML via GoogleTest
    [~] Add filesystem policy: temp working dir, RO mounts, stdout/stderr caps
    [~] Implement caching layer keyed by prompt+code+tests+limits hash
    [X] Implement error taxonomy parser for compile, link, runtime, timeout, and policy violations
    [ ] Create malicious sample integration tests (file read, fork bomb, excessive forks, socket open)

** [ ] Phase 5: Reward Shaping and Safety Gates
    [X] Implement reward aggregator with weighted compile/link status, tests, and coverage signals
    [X] Integrate clang-tidy/clang++ -Wall -Wextra -Werror diagnostics into normalized lint score
    [X] Integrate static analysis (cppcheck) scoring and normalization
    [X] Implement coverage delta computation using gcov/lcov or llvm-cov
    [X] Implement edit-cost, time, and memory penalty functions with clamps
    [X] Add reward histogram logging to tracker with sanity checks
    [X] Add all-green test bonus to reward aggregator

** [~] Phase 6: HRM Training Loop Integration
    [X] Implement CodeEncoder interface and tokenizer utilities for C++ syntax
    [X] Add optional SFT training path on canonical C++ solutions
    [X] Integrate REINFORCE with value baseline and entropy regularization
    [X] Implement curriculum toggles for visible versus hidden tests
    [X] Add checkpointing, resume logic, and deterministic dataloaders
    [X] Create 5-task smoke run pipeline for CI runtime budgets

** [ ] Phase 7: Evaluation Harness and Reporting
    [X] Implement pass\@k computation with fixed seeds and sampling policies
    [X] Implement determinism checker to re-run top-k with shuffled ordering
    [X] Implement flaky-test detector and flagging in results
    [X] Build HTML and Markdown report generator with tables and plots
    [X] Implement baseline comparator against recorded C++ code-LM prompts
    [X] Implement artifact bundler and uploader for reports and raw JSON

** [ ] Phase 8: CI/CD and Automation
    [X] Create GitHub Actions workflow for C++ lint (clang-tidy/clang-format) and unit tests on PRs
    [?] Create CI smoke evaluation job on sample subset with artifacts (ctest + lcov upload)
    [ ] Create nightly full evaluation job with retention and tagging
    [X] Implement version stamping (git SHA, Docker digest, seeds) in runs
    [ ] Configure GitHub Pages publish for latest report artifacts
    [ ] Bootstrap MLflow or W\&B project with tags and run summaries

** [ ] Phase 9: AST-Edit Action Space (v2)
    [X] Integrate Tree-sitter C++ grammar and bindings
    [X] Implement node type schema and AST embedding encoder for C++
    [X] Define edit action space for insert, replace, and delete operations
    [~] Implement cursor policy module for region selection by HRM high-level
    [X] Implement decoder constraint checker to avoid invalid AST states
    [ ] Add ablation job configs and comparison report against token baseline

** [ ] Phase 10: C++ Runner and Codeforces Integration (v2)
    [~] Implement g++/clang++ compile wrapper with optimized flags and diagnostics parsing
    [~] Implement sandbox execution adapter for compiled binaries with sanitizer support (ASan/UBSan)
    [~] Implement Codeforces I/O harness builder and result comparator (multiple test files, TL/ML handling)
    [~] Configure static versus dynamic linking inside jail with rpath handling and ccache
    [ ] Create C++ security test suite for resource abuse and restricted syscalls
    [ ] Integrate C++ metrics and outcomes into common evaluator and reports
