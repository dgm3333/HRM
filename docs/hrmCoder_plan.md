# HRM Coder — Comprehensive Development Overview (C++-Focused)

## 1) High-Level Vision & Scope

**Vision:** Build a reliable, reproducible **C++** HRM-powered coder that synthesizes and repairs programs on deterministic, judge-style benchmarks with **safe native execution**, **stable multi-signal rewards**, and **one-command automation** (data → train → eval).

**In-scope (v1):**

1. Token-level C++ code generation on deterministic **intro competitive-programming** tasks (Codeforces-Intro, AtCoder-ABC subset) and a **HumanEval-CPP** port.
2. Hermetic native execution via **isolate/nsjail/gVisor**, per-job CPU/RAM/wall caps, network-off.
3. Multi-signal reward including **compile/link status, unit/I-O tests, sanitizers, coverage, static-analysis** penalties.
4. CI pipelines; experiment tracking; HTML/Markdown + coverage reports.
5. Early GUI stub to launch runs, stream logs, view artifacts (JUnit XML, llvm-cov HTML).

**Planned (v2+):**

* **AST-edit** action space using **Tree-sitter C++**; grammar-constrained decoding.
* Multi-compiler support (GCC/Clang), Windows cross builds (optional).
* Larger curated sets (Kattis micro-set, more Codeforces difficulty A/B).
* Hardened supply-chain posture (SBOMs, image scanning, reproducible toolchains).

**Out of scope (initial):**

* Internet during execution; system-level tasks needing root; IDE plugins.

---

## 2) Architectural Blueprint (components, data flow, integration)

**Core components**

1. **Datasets & Builders (C++)**

   * **Codeforces-Intro** (A-level): I/O pairs, per-problem TL/ML, deterministic inputs.
   * **AtCoder ABC subset**: normalized I/O samples, stdin/stdout oracle.
   * **HumanEval-CPP**: C++ ports with **GoogleTest** harness (function contracts).
   * Versioning via **DVC**; hashes locked in `data/versions.yml`.

2. **Representation Layer**

   * **v1: Token generation** (`CodeEncoder`, C++-aware tokenizer: operators, punctuation, keywords, identifiers).
   * **v2: AST-edit** (`ASTEncoder` over Tree-sitter C++ nodes; actions = insert/replace/delete with type constraints).

3. **Sandbox Executor (native)**

   * Adapters: `isolate` (primary) and `nsjail`/`gVisor` (alt).
   * Build pipeline: **CMake + g++/clang++**; debug profile with `-fsanitize=address,undefined`, release profile `-O2 -pipe`.
   * Test runners:

     * **GoogleTest (gtest)** for HumanEval-CPP → **JUnit XML**.
     * **I/O judge** for Codeforces/AtCoder (stdin → stdout compare; multiple testfiles).
   * Coverage: **llvm-cov**/**lcov** (per-test and aggregate).
   * Static analysis: **clang-tidy**, **cppcheck** (scored into reward).
   * Caching keyed by `(prompt+code+tests+limits+toolchain)` hash.

4. **Reward Engine (native signals)**

   * Compile/link success, warning budget (normalized from diagnostics).
   * gtest pass ratios; I/O case-by-case micro-rewards; **all-green bonus**.
   * **Sanitizer** cleanliness (ASan/UBSan): failures penalized.
   * Coverage deltas; edit-cost/time/memory penalties.

5. **HRM Trainer**

   * HRM controller + value baseline + entropy reg; optional SFT on canonical C++ solutions.
   * Curriculum: reveal hidden tests later; early stopping on validation pass\@1.

6. **Evaluator & Reporter**

   * Metrics: pass\@1/@10, edits-to-solve, compile/link error rate, timeout rate, sanitizer incidents.
   * Flakiness detector (re-run/shuffle order); regression dashboards; coverage & diagnostics HTML.

7. **Orchestration & CI/CD**

   * Docker images: `runner` (g++, clang, isolate/nsjail, llvm-cov) and `trainer` (CUDA/PyTorch).
   * Hydra configs, Makefile/CMake targets; GitHub Actions; W\&B/MLflow logging.
   * Seeds, git SHA, Docker digest stamped in artifacts.

8. **GUI (Web)**

   * Run Console, Jobs & Artifacts, Dataset Browser, Security & Limits.
   * Artifact viewers: JUnit XML summaries, llvm-cov HTML, diagnostics.

**Data flow (happy path)**

1. Pick config → Hydra resolves → seeds fixed.
2. Builder emits problem bundle (prompt, starter, tests, oracle, TL/ML) → DVC snapshot.
3. HRM proposes code (tokens/edits) → write sources & harness.
4. Executor builds/runs in sandbox → JUnit XML + I/O verdicts + coverage + logs.
5. Reward engine aggregates signals → trainer updates HRM.
6. Evaluator recomputes pass\@k & determinism checks.
7. Reporter publishes HTML/MD & coverage; tracker logs parameters/metrics.

**Key integrations**

* **Tree-sitter C++**, **GoogleTest/ctest**, **clang-tidy/cppcheck**, **llvm-cov**.
* **isolate/nsjail/gVisor**; **Hydra, DVC, W\&B/MLflow, GitHub Actions**.

---

## 3) Phase-by-Phase Roadmap (major milestones)

1. **P0 – Discovery & Reuse audit**
   Audit HRM repo/paper; evaluate isolate/nsjail; pick compilers and coverage stack.
2. **P1 – Repo scaffold & deterministic env**
   Docker toolchains, Makefile/CMake, Hydra, pre-commit (clang-format/tidy).
3. **P2 – GUI stub + backend skeleton**
   FastAPI + simple web UI; artifact viewers for JUnit/coverage.
4. **P3 – Deterministic dataset pipeline (C++)**
   Codeforces-Intro, AtCoder ABC, HumanEval-CPP; DVC; determinism checks.
5. **P4 – Sandbox executor (C++)**
   Build/run adapters; gtest + I/O judge; coverage; caching.
6. **P5 – Reward shaping & safety gates**
   Diagnostics, sanitizers, static analysis, coverage deltas.
7. **P6 – HRM training loop integration**
   C++ tokenization, SFT (optional), RL w/ baseline, curriculum.
8. **P7 – Evaluation harness & reports**
   pass\@k, flakiness, sanitizer dashboards, HTML/MD.
9. **P8 – CI/CD & automation**
   PR smoke ctest; nightly eval; artifact publishing.
10. **P9 – AST-edit (v2)**
    Tree-sitter C++; typed edits; ablations vs token.
11. **P10 – Extended judges (v2)**
    More I/O tasks; multi-file builds; static/dynamic linking in jail.

---

## 4) GUI Description (C++ artifacts)

* **Run Console:** dataset pickers, toolchain (GCC/Clang), build type (Sanitized/Release), TL/ML overrides, reward weights, sandbox limits. Buttons: *Dry-run 3*, *Train*, *Evaluate*, *Report*. Live logs.
* **Jobs & Artifacts:** status, metrics, sanitizer incidents, coverage %, links to **JUnit**, **llvm-cov HTML**, build logs, emitted binaries’ hashes.
* **Dataset Browser:** view per-problem statement (shortened), TL/ML, oracle baseline, determinism flag.
* **Security & Limits:** view sandbox profile (caps/seccomp), memory/CPU quotas, filesystem mounts.

Stubbed early with mock run objects and static artifact samples.

---

## 5) Detailed Task/Phase Breakdown

### P0 – Discovery & Reuse Audit

* Inventory HRM APIs for code-token/AST edit integration.
* Compare **isolate** vs **nsjail** vs **gVisor**; choose default + fallbacks.
* Select toolchain: GCC 13+/Clang 17+, **llvm-cov**; decide sanitizer matrix.
* Toolchain detection utility (`runners/toolchain_detector.py`) reports available compilers and coverage tools.
* Dataset curation plan, licenses, and contamination checks.
* Threat model for native execution; initial sandbox policy.
* ADRs for sandbox, tracker, GUI stack; risk register.

### P1 – Repo Scaffold & Deterministic Env

* Layout: `conf/`, `hrm/`, `runners/`, `datasets/`, `cpp/` (harness templates), `scripts/`, `tests/`, `docs/`.
* `runner.Dockerfile`: g++, clang++, cmake, ninja, isolate/nsjail, llvm-cov, cppcheck, clang-tidy.
* `trainer.Dockerfile`: CUDA+PyTorch (pinned), Python deps, seeds/determinism flags.
* Makefile: `data`, `build_runner`, `train`, `eval`, `report`.
* CMake presets: `Sanitized` (`-O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer`), `Release` (`-O2 -pipe`), `Warnings` (`-Wall -Wextra -Werror`).
* Pre-commit: **clang-format**, **clang-tidy**, **codespell**; Python aux tools lint.
* Env pinning: container digests; deterministic locale/TZ.

### P2 – GUI Stub + Backend Skeleton

* **FastAPI** endpoints: `/runs`, `/train`, `/eval`, `/logs/ws`, `/artifacts/*`.
* Front-end: Run Console & Jobs list; artifact viewers (JUnit summary, llvm-cov HTML).
* WebSocket log tail; mock runs; quickstart docs.

### P3 – Deterministic Dataset Pipeline (C++)

* **HumanEval-CPP** builder: function signatures, reference solutions, `gtest` cases.
* **Codeforces-Intro** builder: parse HF dumps/CSV; produce stdin files & expected stdout; per-problem TL/ML.
* **AtCoder ABC** builder: normalized I/O harness.
* Determinism validator: re-run → identical verdicts/hashes; record toolchain.
* DVC pipelines; schema contracts & unit tests; seeded splits.
  `scripts/generate_dvc_yaml.py` emits the DVC stage tying the catalog to
  `build_from_catalog` with `versions.yml` locks.

### P4 – Sandbox Executor (C++)

* `isolate.py` adapter (or `nsjail.py`) with CPU/ML/TL/FD caps; network-off; RO mounts.
* Build wrapper: CMake configure+build; compile/link diagnostics parsing.
* Test runners:

  * `gtest_runner`: produce **JUnit XML**, capture stdout/stderr caps.
  * `io_judge`: iterate testfiles, enforce TL per case, diff outputs (whitespace policy).
* Coverage collection with **llvm-profdata**/**llvm-cov** or **lcov**; HTML export.
* Cache on `(prompt, code, tests, limits, toolchain)`; error taxonomy (compile/link/runtime/timeout/sanitizer/policy).
* Adversarial tests: fork bombs, unbounded memory, file/network, `/proc` traversal → must be denied.

### P5 – Reward Shaping & Safety Gates

* Reward = weighted sum:

  * Compile/link status (gate).
  * **Diagnostics budget**: normalize warnings/errors (clang-tidy, `-Wall/-Wextra`).
  * Unit/I-O micro-rewards; **all-green** bonus.
  * **Sanitizer** clean run bonus; sanitizer crash penalty.
  * Coverage delta (lines/branches covered).
  * Edit/time/memory penalties (near-limit penalties).
* Histograms & drift checks; unit tests with golden JUnit/coverage → expected reward.

### P6 – HRM Training Loop Integration

* **C++ tokenizer** rules (operators, templates, literals, comments stripped).
* `CodeEncoder` implemented; `ASTEncoder` interface drafted.
* Optional **SFT** on canonical C++ solutions (1–2 epochs).
* RL: REINFORCE + value baseline, entropy reg, grad clip; KL leash (optional EMA teacher).
* Curriculum toggles (visible → hidden tests); checkpoint/resume; seeded data loaders.
* CI smoke run: 5 tasks E2E with Sanitized build.

### P7 – Evaluation Harness & Reports

* pass\@1/@10 with fixed seeds; timeout & sanitizer incident rates.
* Determinism checker (repeat with shuffled order).
* Flakiness detector (variance across re-runs).
* HTML/MD reports: tables, spark-lines; links to JUnit, coverage, logs.
* Baselines: small C++ code-LM prompting on same subsets.

### P8 – CI/CD & Automation

* GitHub Actions:

  * **PR**: clang-format/tidy, unit tests, 3-problem smoke eval, artifact upload.
  * **Nightly**: full eval matrix (GCC/Clang × Sanitized/Release), W\&B summary.
* Version stamping (git SHA, Docker digest, seeds); GitHub Pages for latest report.
* MLflow/W\&B project setup (tags, configs, metrics).

### P9 – AST-Edit (v2)

* Tree-sitter C++ integration; node embeddings (type, depth, parent chain).
* Typed action space; constraint checker (no invalid states).
* Cursor policy: HRM high-level selects region; low-level applies atomic edit.
* Ablations vs token baseline; edits-to-solve comparison; report.

### P10 – Extended Judges & Linking (v2)

* Multi-file projects; library stubs; automatic `$ORIGIN` rpath handling for dynamic builds in jail.
* Optional **static** builds where feasible; **ccache** for speed.
* Additional datasets (Kattis micro-set) with license review.
* Security suite expansion (syscall denylist regression).

---

## 6) Testing & Validation Strategy

**Code quality**

* Pre-commit: **clang-format**, **clang-tidy**, **cppcheck**, **codespell** (and Python lint for orchestration).
* Unit tests: dataset builders, executor adapters, reward math, evaluators.
* Contract tests: Hydra config schema; CMake presets; toolchain presence.

**Integration & E2E**

* CI **smoke**: build+run 5 tasks (gtest + I/O) in **Sanitized** mode.
* Replay determinism: identical verdicts/hashes with same seed/toolchain.

**Performance & Reliability**

* Enforce TL/ML caps; executor throughput metrics; cache hit-rate KPI.
* Compiler cache (ccache) for iterative runs.

**Security**

* Threat model; adversarial sample suite (fork, mmap flood, sockets, `/proc`).
* Container scan & SBOM; immutable base image digests.
* Sandbox profiles versioned and tested.

**Determinism**

* Pin compiler versions; lock container digests; stable locale/TZ.
* Double-run determinism check on evaluation; fail CI on divergence.

**Acceptance (v1)**

* pass\@1 ≥ target on Codeforces-Intro + HumanEval-CPP.
* 0 sandbox escapes; sanitizer-clean PR smoke; “one-command demo” green.

---

## 7) Documentation Plan

**User-facing**

* Quickstart (CLI & GUI) with screenshots.
* One-command demo guide.
* Runbook: toolchains, sanitizer modes, common errors, TL/ML tuning.

**Developer**

* Architecture overview diagram.
* ADRs: sandbox, reward signals, coverage stack, GUI stack.
* API reference (hrm integration, executor, builders).
* Contribution guide: code style, tests, CI, release.

**Compliance & Reproducibility**

* Threat Model & Sandbox Policy (caps, seccomp, mounts).
* Reproducibility SOP (seeds, container digests, hashing scheme).
* Dataset lineage (DVC graphs, licenses).
* Model card (intended use, metrics, limitations).

**Reporting**

* Automated HTML/MD with links (JUnit, coverage, logs, configs).
* Changelog per release tag.

---

## Appendix — Suggested Repository Layout (C++-aware)

```
hrm-coder/
  conf/                      # Hydra configs (dataset/model/reward/sandbox/toolchain)
  docker/
    runner.Dockerfile        # g++, clang++, cmake, isolate/nsjail, llvm-cov, tidy
    trainer.Dockerfile       # CUDA + PyTorch, pinned
  hrm/                       # HRM integration (CodeEncoder, ASTEncoder)
  runners/
    isolate.py               # sandbox adapter
    nsjail.py                # optional adapter
    cpp_build.py             # cmake/ninja wrappers, diagnostics parsing
    gtest_runner.py          # runs gtest, emits JUnit
    io_judge.py              # stdin/stdout runner for I/O tasks
  cpp/
    harness/                 # gtest templates, main.cc
    cmake/                   # toolchain files, presets
  datasets/
    humaneval_cpp.py         # builder + refs + gtest gen
    codeforces.py            # I/O harness generator + TL/ML
    atcoder_abc.py           # I/O builder
  orchestration/             # FastAPI backend, GUI assets
  scripts/                   # make_data.sh, train.sh, eval.sh, report.py
  tests/                     # unit/integration/security tests
  reports/                   # generated HTML/MD/coverage
  docs/                      # mkdocs or sphinx source
```

---

## Milestone Exit Criteria (condensed)

* **M1 (Token baseline working/C++):** Deterministic executor, gtest & I/O judges, reports generated.
* **M2 (Reliable rewards):** Diagnostics/sanitizer/static-analysis integrated; CI smoke all-green.
* **M3 (GUI usable):** Launch runs, stream logs, view JUnit/coverage.
* **M4 (AST-edit ready):** Tree-sitter C++; measurable edits-to-solve change.
* **M5 (Extended judges):** Multi-file C++ projects, robust linking, expanded datasets.
