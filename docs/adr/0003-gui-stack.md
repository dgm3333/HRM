# 0003: GUI Stack

## Status
Accepted

## Context
A minimal web interface is required for launching runs and viewing artifacts. Options include full-featured frameworks or lightweight stacks.

## Decision
Use **FastAPI** for the backend with a simple HTML/JavaScript frontend built with **htmx** and **Tailwind CSS**. This keeps the stack lightweight while enabling interactive pages and WebSocket log streaming.

## Consequences
- The GUI shares Python dependencies with the backend runner, simplifying development.
- htmx keeps the frontend mostly server-rendered, avoiding a large SPA build toolchain.
- Tailwind CSS provides basic styling without hand-written CSS.
