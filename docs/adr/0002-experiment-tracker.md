# 0002: Experiment Tracker

## Status
Accepted

## Context
Training runs must be reproducible and comparable. A lightweight experiment tracker will log metrics, parameters, and artifacts.
Options considered were **Weights & Biases** (W&B) and **MLflow**.

## Decision
Adopt **MLflow** for the initial implementation. It is open-source, self-hostable, and integrates well with Python tooling used in HRM Coder.

## Consequences
- MLflow server will be bundled with development docker compose for easy startup.
- Future work may add optional W&B integration for cloud-based tracking.
- Artifacts such as coverage reports and reward logs are stored under the MLflow run directory.
