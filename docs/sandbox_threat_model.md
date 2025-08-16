# Sandbox Threat Model

This document outlines potential threats when executing untrusted native binaries during HRM Coder development.

## Assets
- Host operating system and other processes
- Dataset integrity and evaluation results
- Credentials and network isolation guarantees

## Assumptions
- Attackers can supply arbitrary C++ code snippets that are compiled and executed.
- Sandboxing tools are available on the host (`isolate`, `nsjail`, or `runsc`).
- Network access inside the sandbox is disabled.

## Threats
1. **Escaping the sandbox** via kernel vulnerabilities or misconfiguration.
2. **Resource exhaustion** such as fork bombs or excessive memory use.
3. **Filesystem access** beyond the working directory, including `/proc` or host mounts.
4. **Network access** attempts despite policy to remain offline.
5. **Abuse of privileged syscalls** leading to privilege escalation.

## Security Requirements
- Enforce strict CPU, memory, and wall-clock limits.
- Run binaries as a non-root user with minimal capabilities.
- Mount only a temporary working directory with read-only source files.
- Apply seccomp or similar syscall filters restricting networking and dangerous operations.
- Ensure repeatability: sandbox configuration is declarative and version controlled.

## Mitigations
- Prefer `isolate` as the default sandbox; fall back to `nsjail` or `runsc` if available.
- Run integration tests using intentionally malicious samples to verify containment.
- Log sandbox diagnostics and enforce zero-tolerance for escapes or policy violations.
