# 0003: GUI Stack

## Status
Accepted

## Context
A minimal web interface is required for launching runs and viewing artifacts. We
considered heavy single-page-app frameworks versus lighter, mostly
server-rendered approaches.

## Decision
Use **FastAPI** for the backend with a simple HTML/JavaScript frontend built
with **htmx** and **Tailwind CSS**. This keeps the stack lightweight while
enabling interactive pages and WebSocket log streaming without a separate build
step.

## Consequences
- The GUI shares Python dependencies with the backend runner, simplifying
  development.
- htmx keeps the frontend mostly server-rendered, avoiding a large SPA build
  toolchain.
- Tailwind CSS provides basic styling without hand-written CSS.
