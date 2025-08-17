# Sandbox Threat Model

This document outlines potential threats when executing untrusted native binaries during HRM Coder development.

## Assets
- Host operating system, kernel, and hardware resources
- Build toolchain, compiler caches, and temporary artifacts
- Dataset integrity, evaluation results, and MLflow tracking data
- Credentials, secrets, and network isolation guarantees

## Assumptions
- Attackers can supply arbitrary C++ code snippets that are compiled and executed.
- Sandboxing tools are available on the host (`isolate`, `nsjail`, or `runsc`).
- Network access inside the sandbox is disabled.

## Threats
1. **Escaping the sandbox** via kernel vulnerabilities, misconfiguration, or symlink/mount tricks.
2. **Resource exhaustion** such as fork bombs, uncontrolled threads, or excessive memory use.
3. **Filesystem access** beyond the working directory, including `/proc`, device nodes, or host mounts.
4. **Network access** attempts despite policy to remain offline or to exfiltrate data.
5. **Abuse of privileged syscalls** leading to privilege escalation or capability leakage.
6. **Compiler or linker manipulation** to inject malicious build scripts or preload shared objects.

## Security Requirements for Native Binaries
- Enforce strict CPU, memory, and wall-clock limits for each run.
- Execute as a non-root user with dropped capabilities and a separate mount namespace.
- Provide only a temporary working directory with read-only source and toolchain files.
- Apply seccomp or similar syscall filters restricting networking, filesystem, and process-control operations.
- Validate compiler and linker inputs; allow linking only against approved libraries.
- Ensure reproducibility: sandbox configuration and limits are version controlled.

## Mitigations
- Prefer `isolate` as the default sandbox; fall back to `nsjail` or `runsc` if available.
- Run integration tests using intentionally malicious samples to verify containment.
- Log sandbox diagnostics and enforce zero-tolerance for escapes or policy violations.
