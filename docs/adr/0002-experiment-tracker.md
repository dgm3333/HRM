# 0002: Experiment Tracker

## Status
Accepted

## Context
Training runs must be reproducible and comparable. A lightweight experiment
tracker will log metrics, parameters, and artifacts. Two candidates were
evaluated:

* **Weights & Biases (W&B)** – excellent hosted UI and collaboration features
  but requires external services for self‑hosting.
* **MLflow** – open source with a simple local file backend and optional server
  mode.

## Decision
Adopt **MLflow** for the initial implementation. It is open-source,
self-hostable, and integrates well with Python tooling and Hydra configs used in
HRM Coder.

## Consequences
- MLflow server will be bundled with development docker compose for easy
  startup.
- Future work may add optional W&B integration for cloud-based tracking.
- Artifacts such as coverage reports and reward logs are stored under the MLflow
  run directory.
