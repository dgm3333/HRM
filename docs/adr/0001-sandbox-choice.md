# 0001: Sandbox Choice

## Status
Accepted

## Context
HRM Coder needs a sandbox to execute untrusted C++ binaries safely. Options include `isolate`, `nsjail`, and `runsc` from gVisor.

## Decision
Use **isolate** as the default sandbox backend. Keep **nsjail** and gVisor's **runsc** available as fallbacks to aid portability and testing.

## Consequences
- `isolate` becomes a hard dependency for runner images.
- Additional adapters for `nsjail` and `runsc` allow experiments on platforms where `isolate` is unavailable.
- The choice influences security policies and integration tests in later phases.
