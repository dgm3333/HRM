# 0001: Sandbox Choice

## Status
Accepted

## Context
HRM Coder needs a sandbox to execute untrusted C++ binaries safely. We
evaluated three mature options that provide process isolation with CPU and
memory limits:

* **isolate** – small C utility used in IOI/CMS with good documentation and low
  overhead.
* **nsjail** – feature rich, but requires more configuration and has a larger
  surface area.
* **runsc** (gVisor) – strongest isolation using a user-space kernel, but
  heavier to integrate and slower for short‑lived jobs.

## Decision
Use **isolate** as the default sandbox backend. It offers the simplest
integration while providing deterministic CPU, memory, and wall time limits. We
will keep **nsjail** and gVisor's **runsc** adapters available as fallbacks to
aid portability and benchmarking on platforms where isolate is unavailable.

## Consequences
- `isolate` becomes a hard dependency for runner images.
- Additional adapters for `nsjail` and `runsc` allow experiments on platforms where `isolate` is unavailable.
- The choice influences security policies and integration tests in later phases.
