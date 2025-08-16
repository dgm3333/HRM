# HRM Coder GUI Quickstart

This stub GUI exposes a FastAPI backend for managing training and evaluation runs.

## Running the server

```
uvicorn hrm_coder:app --reload
```

## Example usage

```
# List runs
curl http://localhost:8000/runs

# Start a training run
curl -X POST http://localhost:8000/train -H 'Content-Type: application/json' -d '{}'
```
