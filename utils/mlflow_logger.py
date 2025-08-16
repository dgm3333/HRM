from __future__ import annotations

"""Convenience wrappers around MLflow for HRM Coder.

This module provides light-weight helpers to start MLflow runs with
standard tags and to log parameters or metrics.  The tracking URI
defaults to a local ``mlruns`` directory in the repository root when
``MLFLOW_TRACKING_URI`` is not set.
"""

import os
import pathlib
from typing import Any, Dict, Optional

import mlflow


def start_run(run_name: str, tags: Optional[Dict[str, str]] = None) -> None:
    """Start an MLflow run and apply default tags.

    Parameters
    ----------
    run_name:
        Human-readable identifier for the run.
    tags:
        Additional tag key/value pairs to attach to the run.
    """
    if "MLFLOW_TRACKING_URI" not in os.environ:
        repo_root = pathlib.Path(__file__).resolve().parents[1]
        mlflow.set_tracking_uri((repo_root / "mlruns").as_uri())
    mlflow.set_experiment("hrm-coder")
    mlflow.start_run(run_name=run_name)
    base_tags = {"project": "hrm-coder"}
    if tags:
        base_tags.update(tags)
    mlflow.set_tags(base_tags)


def log_params(params: Dict[str, Any]) -> None:
    """Log a collection of parameters to the current run."""
    mlflow.log_params(params)


def log_metrics(metrics: Dict[str, float]) -> None:
    """Log a collection of metrics to the current run."""
    mlflow.log_metrics(metrics)


def end_run() -> None:
    """Terminate the active MLflow run."""
    mlflow.end_run()
