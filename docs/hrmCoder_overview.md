
# HRM Coder

* Public HRM work (paper + repo) shows Sudoku, mazes, and ARC; no code benchmarks or encoders yet. ([arXiv][1], [GitHub][2])

# 1) Objectives

* **Robustness:** no flakiness; identical results on re-runs.
* **Reliability:** safe execution of arbitrary code; explicit limits.
* **Automation:** one-command data build → train → eval; CI checks; experiment tracking.

# 2) End-to-end architecture (high level)

* **Data layer:** curated mini-benchmarks (HumanEval subset, MBPP subset, small Codeforces split), versioned with DVC; all prompts + tests normalized. ([GitHub][3], [Hugging Face][4], [arXiv][5])
* **Representation:** start with **token-level** decoder; optionally add **AST-edit** action space via Tree-sitter for syntax-safe edits. ([tree-sitter.github.io][6], [GitHub][7])
* **Executor:** hermetic sandbox runner (nsjail/isolate or Docker+gVisor), per-job CPU/RAM/wall limits, network off, read-only FS. ([GitHub][8], [gvisor.dev][9])
* **Reward:** multi-signal (compile, lint/type check, unit tests by shard, coverage deltas); shaped and stable.
* **Trainer:** HRM as-is (two recurrent modules); RL head with advantage baseline, entropy reg; optional SFT warm-start from canonical solutions.
* **Evaluator:** pass\@k, determinism checks, flaky-test detector, regression dashboards.
* **Orchestration:** Dockerfile + Makefile + Hydra configs; W\&B/MLflow; GitHub Actions.

# 3) Datasets (small but clean)

Start tiny and verifiable; each sample has `{prompt, starter, tests, reference}`.

* **HumanEval-S (≈40 tasks):** ensure deterministic tests (no `random`, no network/time). ([GitHub][3], [Hugging Face][4])
* **MBPP-S (≈100 tasks):** keep tasks solvable < \~80 tokens or ≤ 10 edit-steps; convert doctests→pytest. ([arXiv][5], [GitHub][10])
* **Codeforces-Intro (≈100 A-level):** use an open HF dump (input→output harness), wrap with I/O runner. ([Hugging Face][11])
* Version all artifacts with **DVC** and lock dataset hashes in `data/versions.yml`.

Augmentation (to reach \~1k samples without contamination):

* Prompt paraphrases (docstring wording), **but never** mutate tests or logic.
* **Bug injection** for repair tasks (swap ops, off-by-one) to teach edit-based fixes.

# 4) Representation options (pick 1 to start, keep 2 as “Phase-2”)

**A. Token generation (baseline)**

* BPE tokenizer (32k code vocab). Keep HRM decoder unchanged.

**B. AST-edit actions (more reliable syntax)**

* Build grammar with Tree-sitter; actions = {insert, replace, delete} over typed nodes; cursor = high-level module proposes region (“implement loop over array”), low-level does local edit. Consider grammar/type-constrained decoding to avoid invalid states. ([tree-sitter.github.io][6], [NeurIPS Proceedings][12], [arXiv][13])

# 5) Secure, deterministic execution

* **Sandbox:** choose **nsjail** or **isolate** (used in IOI/CMS) for per-run limits; alternative: Docker with `--runtime=runsc` (gVisor). Disable network; tmpfs; CPU quota; memory+pid limits; seccomp/caps. ([GitHub][8], [cms.readthedocs.io][14], [gvisor.dev][15])
* **Runners:** language-specific:

  * Python: `pytest -q` inside sandbox; `pytest-timeout` plugin; cap stdout/stderr. ([Pytest Documentation][16], [LambdaTest][17])
  * C++ (Phase-2): compile with `g++ -O2 -pipe -static -s` (if available) or dynamic with `$ORIGIN` rpath inside the jail; optional `ccache` for speed; run with the same limits (use isolate “box”). ([ucw.cz][18])
* **Caching:** hash(prompt+partial\_code+tests) → avoid re-running identical shards.
* **Stability:** fix `PYTHONHASHSEED`, locale, time zone; no wall-clock in tests.

# 6) Reward shaping (beyond binary pass/fail)

Signals (0–1 scaled), averaged with tuned weights:

* **Compile/runtime status** (fails = 0, success = 0.1).
* **Lint/type checks** (e.g., `flake8`/`mypy` for Py; `-Wall -Werror` for C++), normalized to \[0, 0.1]. (Security SAST like Bandit optional.) ([GitHub][19], [bandit.readthedocs.io][20])
* **Unit tests:** test-by-test micro-rewards (each pass gives incremental credit) + a **bonus** for all-green.
* **Coverage delta:** reward increases if new failing tests turn green (less sparse).
* **Edit cost penalty:** discourage thrashing; small negative per token/edit.
* **Time/mem penalty:** subtract if near limits.

# 7) Training loop (HRM + stable RL)

* **Warm-start (optional):** SFT on canonical solutions for 1–2 epochs to learn idioms.
* **HRM RL:** REINFORCE **with baseline** (value head over HRM state) + entropy regularization; gradient clipping; KL leash if you keep an EMAs teacher.
* **Curriculum:** start with “unit-tests visible”; later hide them (black-box) to generalize.
* **Early stop:** monitor pass\@1 on a held-out validation set; stop on plateau.
* **Reproducibility:** seed everything; set CuDNN deterministic flags; pin wheels/conda env.

# 8) Evaluation you can trust

* **Metrics:** pass\@1/@10, mean edits-to-solve, sandbox timeouts, syntax-error rate.
* **Determinism check:** re-run top-k candidates with different orderings → flag flakiness.
* **Ablations:** token vs AST actions; with/without reward shaping; SFT vs none.
* **Baselines:** small code-LM with CoT/on-policy sampling on the same subsets (HumanEval-S, MBPP-S) for relative gains. ([Evidently AI][21])
* **Reports:** auto-publish HTML/Markdown with tables + W\&B links; store raw JSON.

# 9) Automation & CI/CD

* **Repo layout**

  ```
  hrm-coder/
    conf/              # Hydra configs (dataset, model, runner, reward)
    docker/            # Dockerfiles (runner, trainer)
    hrm/               # your forked HRM + encoders (CodeEncoder, ASTEncoder)
    runners/           # sandbox adapters: nsjail.py, isolate.py, gvisor.py
    datasets/          # builders: humaneval.py, mbpp.py, codeforces.py
    scripts/           # make_data.sh, train.sh, eval.sh, report.py
    tests/             # unit tests for the harness itself
  ```
* **Docker images**

  * `trainer`: CUDA + PyTorch + HRM deps (pins from HRM README; FlashAttention as needed). ([GitHub][2])
  * `runner`: minimal runtime per language + nsjail/isolate binaries.
* **Make/Hydra**

  * `make data DATASET=mbpp-s`
  * `make train CFG=token_baseline`
  * `make eval CKPT=...`
* **GitHub Actions**

  * Lint & unit tests for harness.
  * “Dry-run” eval on 5 samples (smoke test).
  * Nightly full eval; upload artifacts to W\&B/MLflow + GitHub Pages.
* **Experiment tracking:** W\&B or MLflow; log seeds, git SHA, Docker digest.

# 10) Implementation notes (key diffs from your draft)

* **Encoder:** keep your `CodeEncoder` for v1; add `ASTEncoder` in v2 using Tree-sitter to emit node embeddings (type + depth + parent chain). ([tree-sitter.github.io][6])
* **Reward runner:** replace ad-hoc `subprocess.run("python file.py")` with a **sandbox adapter**:

  * creates temp dir, writes `prompt + code + tests`,
  * invokes `pytest -q` (or compiled binary) **inside** nsjail/isolate,
  * enforces hard caps (e.g., 2 vCPU, 256MB, 5s, no net),
  * parses JUnit XML for per-test rewards.
* **Safety:** never execute outside sandbox; ban `__import__`, `open`, etc., via policies even for Python. (nsjail profiles + Bandit scan) ([GitHub][8], [bandit.readthedocs.io][20])
* **Determinism:** normalize env; strip non-deterministic tests; pin package versions.
* **Evaluation harness:** mirror HumanEval/MBPP official load/eval rules to avoid metric drift. ([GitHub][3], [arXiv][5])

# 11) Milestones

1. **Minimal token baseline** on HumanEval-S with sandboxed pytest; pass\@k + logs.
2. **Reward shaping** + flakiness detector + HTML report.
3. **AST-edit** actions via Tree-sitter; compare edits-to-solve vs token baseline.
4. **C++ runner** (compile + gVisor/isolate); small Codeforces-Intro split.
5. **Release**: Docker images, config presets, and a one-command demo.

# 12) References (for decisions in this plan)

* HRM paper + repo (tasks are puzzles/ARC; no code adapters/checkpoints). ([arXiv][1], [GitHub][2])
* HumanEval / MBPP / APPS / Codeforces datasets. ([GitHub][3], [Hugging Face][4], [arXiv][5])
* Sandboxing options: nsjail (used in snekbox), isolate (IOI/CMS), Docker+gVisor. ([GitHub][8], [cms.readthedocs.io][14], [gvisor.dev][9])
* Grammar/AST constraints for reliable code generation. ([ACL Anthology][22], [NeurIPS Proceedings][12], [arXiv][13])

---

If you want, I can sketch the concrete files (Hydra configs, `nsjail` profile, and a `reward_runner.py` with pytest+JUnit parsing) so you can drop them straight into a `hrm-coder/` fork.

[1]: https://arxiv.org/abs/2506.21734?utm_source=chatgpt.com "Hierarchical Reasoning Model"
[2]: https://github.com/sapientinc/HRM "GitHub - sapientinc/HRM: Hierarchical Reasoning Model Official Release"
[3]: https://github.com/openai/human-eval?utm_source=chatgpt.com "openai/human-eval: Code for the paper \"Evaluating Large ..."
[4]: https://huggingface.co/datasets/openai/openai_humaneval?utm_source=chatgpt.com "openai/openai_humaneval · Datasets at Hugging Face"
[5]: https://arxiv.org/pdf/2108.07732?utm_source=chatgpt.com "Program synthesis with large language models"
[6]: https://tree-sitter.github.io/?utm_source=chatgpt.com "Tree-sitter: Introduction"
[7]: https://github.com/tree-sitter/tree-sitter?utm_source=chatgpt.com "tree-sitter/tree-sitter: An incremental parsing system for ..."
[8]: https://github.com/python-discord/snekbox?utm_source=chatgpt.com "python-discord/snekbox: Easy, safe evaluation of arbitrary ..."
[9]: https://gvisor.dev/docs/user_guide/quick_start/docker/?utm_source=chatgpt.com "Docker Quick Start"
[10]: https://github.com/google-research/google-research/blob/master/mbpp/README.md?utm_source=chatgpt.com "google-research/mbpp/README.md at master"
[11]: https://huggingface.co/datasets/open-r1/codeforces?utm_source=chatgpt.com "open-r1/codeforces · Datasets at Hugging Face"
[12]: https://proceedings.neurips.cc/paper_files/paper/2024/file/2bdc2267c3d7d01523e2e17ac0a754f3-Paper-Conference.pdf?utm_source=chatgpt.com "Grammar-Aligned Decoding"
[13]: https://arxiv.org/abs/2502.05111?utm_source=chatgpt.com "Flexible and Efficient Grammar-Constrained Decoding"
[14]: https://cms.readthedocs.io/_/downloads/en/v1.4/pdf/?utm_source=chatgpt.com "CMS Documentation"
[15]: https://gvisor.dev/docs/architecture_guide/intro/?utm_source=chatgpt.com "Introduction to gVisor security"
[16]: https://docs.pytest.org/en/stable/how-to/usage.html?utm_source=chatgpt.com "How to invoke pytest"
[17]: https://www.lambdatest.com/blog/pytest-timeouts/?utm_source=chatgpt.com "How to Handle pytest Timeouts"
[18]: https://www.ucw.cz/isolate/isolate.1.html?utm_source=chatgpt.com "ISOLATE(1)"
[19]: https://github.com/PyCQA/bandit?utm_source=chatgpt.com "PyCQA/bandit: Bandit is a tool designed to find common ..."
[20]: https://bandit.readthedocs.io/?utm_source=chatgpt.com "Welcome to Bandit — Bandit documentation"
[21]: https://www.evidentlyai.com/blog/llm-coding-benchmarks?utm_source=chatgpt.com "10 LLM coding benchmarks"
[22]: https://aclanthology.org/2023.emnlp-main.674.pdf?utm_source=chatgpt.com "Grammar-Constrained Decoding for Structured NLP Tasks ..."
