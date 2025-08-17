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
    [X] Setup project operation within isolate/gVisor runner images
        - Added run_in_sandbox utility script for executing commands in the selected sandbox backend
        - Documented auto-detect helper and sandbox smoke test
    [X] Evaluate isolate and gVisor adapters against nsjail for reuse and gaps
        - Added sandbox detection utility for isolate, nsjail, and gVisor runsc runtime
        - Added default sandbox selection helper to prefer isolate and fall back to nsjail or runsc
        - Integrated sandbox auto-selection into runner configuration
        - Added toolchain detection utility for g++, clang++, lcov, llvm-cov, and gcov
        - Added sandbox smoke test script to verify basic command execution in available backends
        - Added audit CLI with optional JSON output for programmatic environment checks
        - Added environment variable and output limit support to gVisor runner
        - Documented feature parity matrix for isolate, nsjail, and gVisor adapters
        - Added integration tests verifying resource limit enforcement across adapters
        - Implemented file size limit enforcement support in gVisor runner
    [X] Compile dataset catalog (Codeforces-Intro, AtCoder ABC subset, Kattis micro-set, HumanEval-CPP port) with licenses and hashes (see docs/dataset_catalog.json)
        - Added dataset catalog utility with hash validation and unit tests
        - Populated dataset licenses and SHA256 hashes in docs/dataset_catalog.json
    [X] Define acceptance metrics and thresholds for C++ (pass\@k, sanitizer-clean runs, timeout rate)
    [X] Draft sandbox Threat Model and initial security requirements for native binaries
        - Added sandbox threat model doc outlining assets, actors, threats, and mitigations
    [X] Write ADRs for sandbox choice, experiment tracker, and GUI stack
        - Added ADR 0001 detailing isolate as default sandbox with nsjail/runsc fallbacks
        - Added ADR 0002 selecting MLflow for experiment tracking
        - Added ADR 0003 choosing FastAPI with htmx/Tailwind for the GUI stack
    [X] Create initial risk register and mitigation plan
        - Added and reviewed initial risk register and mitigation plan docs

** [ ] Phase 1: Repo Scaffold & Deterministic Environment
    [X] Generate project layout scaffold script for hrm-coder directory tree
    [X] Author runner.Dockerfile with g++, CMake, GoogleTest, isolate/nsjail, and sanitizer toolchain
        - Installed coverage utilities and compiled gtest; locale/timezone pinned for determinism
    [X] Author trainer.Dockerfile with CUDA, PyTorch, and deterministic flags
        - Pinned PyTorch 2.2.0 with CUDA 12.1 runtime and enforced reproducibility flags
    [~] Create Makefile targets for data, train, eval, report, and tooling (CMake + ctest integration)
        - Added build_trainer target for trainer Docker image
        - Added lint target invoking pre-commit hooks
        - Wired data target to dataset.build_from_catalog for deterministic builds
        - Added report target generating Markdown/HTML summaries from evaluation results
        - Added test target running pytest and ctest suites
        - Added tooling target combining lint and test
        - Document train and eval target usage examples
        ~ Add coverage target aggregating ctest and pytest results
    [X] Define Hydra config schema and default configs under conf/
        - Added CPU and memory limit options to runner config defaults
        - Added helper to instantiate sandbox runners from configuration
        - Added network access toggle to runner config defaults
        - Added paths configuration group for dataset, runs, and artifact directories
        - Added unit test covering config loading and path resolution
    [X] Configure pre-commit for C++ (clang-format, clang-tidy, cpplint, codespell) and Python aux tools
        - Added Makefile lint target to run pre-commit
    [X] Implement environment pinning and seed/tz/locale normalization module
    [X] Add minimal CMake build helper for C++ harnesses

** [~] Phase 2: GUI Stub and Backend Skeleton
    [X] Scaffold FastAPI app with /runs, /train, /eval, /logs/ws endpoints
    [X] Implement mock run registry with in-memory store and pagination
    [X] Build Run Console page with config pickers and action buttons
    [X] Build Jobs list page with sortable metrics and artifact links
    [X] Implement artifact static server for JUnit XML and lcov/llvm-cov HTML
    [X] Add WebSocket log streamer with tail-follow behavior
    [X] Provide GUI quickstart docs and sample configs
    [X] Expose coverage summary endpoint and display on run page

** [X] Phase 3: Deterministic Dataset Pipeline (C++)
    [X] Implement HumanEval-CPP builder with harness generator and reference solutions
    [X] Implement Codeforces-Intro builder (I/O testcases, constraints, per-problem time limits)
    [X] Implement AtCoder ABC subset builder with normalized input/output cases
    [X] Implement Kattis micro-set builder for additional I/O tasks
    [X] Write determinism validator to re-run and hash equality of artifacts
    [X] Integrate DVC pipelines and data/versions.yml locking
        - Added version verification utility and catalog build check
        - Added catalog-wide version verification script
        - Added CLI for generating DVC pipeline stage YAML
        - Added convenience script `generate_dvc_yaml.py` for stage creation
    [X] Add dataset schema contracts and unit tests for loaders
    [X] Implement dataset split manager for train/val/test with fixed seeds

** [~] Phase 4: Sandbox Executor
    [X] Implement isolate/nsjail adapter with CPU, RAM, wall time, and net-off policies
        - BinarySandboxAdapter enforces process, memory, and time caps with network disabled by default
    [X] Implement C++ build-and-run pipeline (CMake/g++/clang++) with JUnit XML via GoogleTest
    [X] Add filesystem policy: temp working dir, RO mounts, stdout/stderr caps
    [X] Implement caching layer keyed by prompt+code+tests+limits hash
    [X] Implement standalone I/O judge with whitespace-normalized diff and caching
    [X] Implement error taxonomy parser for compile, link, runtime, timeout, and policy violations
    [X] Create malicious sample integration tests (file read, fork bomb, excessive forks, socket open)

** [?] Phase 5: Reward Shaping and Safety Gates
    [X] Implement reward aggregator with weighted compile/link status, tests, and coverage signals
    [X] Integrate clang-tidy/clang++ -Wall -Wextra -Werror diagnostics into normalized lint score
    [X] Incorporate compiler warning/error counts into reward diagnostics score
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
    [X] Create CI smoke evaluation job on sample subset with artifacts (ctest + lcov upload)
    [X] Create nightly full evaluation job with retention and tagging
    [X] Implement version stamping (git SHA, Docker digest, seeds) in runs
    [X] Configure GitHub Pages publish for latest report artifacts
    [X] Bootstrap MLflow or W\&B project with tags and run summaries

** [~] Phase 9: AST-Edit Action Space (v2)
    [X] Integrate Tree-sitter C++ grammar and bindings
    [X] Implement node type schema and AST embedding encoder for C++
    [X] Define edit action space for insert, replace, and delete operations
    [X] Implement cursor policy module for region selection by HRM high-level
    [X] Implement decoder constraint checker to avoid invalid AST states
    [X] Add ablation job configs and comparison report against token baseline

** [ ] Phase 10: C++ Runner and Codeforces Integration (v2)
    [X] Implement g++/clang++ compile wrapper with optimized flags and diagnostics parsing
        - Default flags: `-std=c++17 -O2 -pipe -Wall -Wextra -fdiagnostics-color=never`
        - Structured parsing of compiler warnings and errors
    [?] Implement sandbox execution adapter for compiled binaries with sanitizer support (ASan/UBSan)
        - Injected default ASAN_OPTIONS and UBSAN_OPTIONS in run_binary for deterministic sanitized runs
        - Added BinarySandboxAdapter to route compiled binaries through sandbox with sanitizer environment
        - Added integration tests exercising BinarySandboxAdapter with nsjail and gVisor backends
        - Documented adapter usage and sanitizer configuration in developer docs
    [?] Implement Codeforces I/O harness builder and result comparator (multiple test files, TL/ML handling)
    [X] Configure static versus dynamic linking inside jail with rpath handling and ccache
        - Added compile wrapper support for include paths, library directories, rpath, optional static builds, and ccache
        - Added helpers for building shared and static libraries to support library stubs in multi-file projects
        - Extended shared library builder with include, library, and rpath options for linking against dependent libraries
        - Implement automatic $ORIGIN-based rpath injection for bundled libraries and binaries
        - Add sandboxed integration tests for dynamic and static linking paths
    [X] Create C++ security test suite for resource abuse and restricted syscalls
    [X] Integrate C++ metrics and outcomes into common evaluator and reports
