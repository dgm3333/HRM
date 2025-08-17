# Sandbox Threat Model

This document outlines threats and mitigations for executing untrusted native
binaries during HRM Coder development.

## Assets
- Host operating system, kernel, and other processes
- Sandbox container image and configuration files
- Dataset integrity and evaluation results
- Credentials and network isolation guarantees
- Build cache and intermediate artifacts

## Assumptions
- Attackers can supply arbitrary C++ code snippets that are compiled and run as
  native binaries.
- Sandboxing tools are available on the host (`isolate`, `nsjail`, or `runsc`).
- Network access inside the sandbox is disabled.
- Compiler toolchains and linked libraries are not implicitly trusted.

## Threat Actors and Capabilities
- Adversaries may embed inline assembly or raw syscalls to bypass runtime
  checks.
- Binaries may attempt to exploit kernel or sandbox vulnerabilities.
- Attackers can generate large outputs or spawn processes to exhaust resources.
- Binaries may try to read or tamper with datasets, caches, or host files.

## Threats
1. **Sandbox escape** via kernel vulnerabilities, misconfiguration, or shared
   mounts.
2. **Resource exhaustion** such as fork bombs, memory blowup, or large files.
3. **Filesystem access** beyond the working directory, including `/proc`,
   symlink traversal, or host mounts.
4. **Network access** despite policy to remain offline.
5. **Abuse of privileged syscalls** (`ptrace`, `mount`, `setuid`, etc.) leading
   to privilege escalation.
6. **Toolchain attacks** where compilers or linker flags modify files outside
   the sandbox.
7. **Side-channel leakage** via residual artifacts or shared caches between
   runs.

## Security Requirements

### Environment
- Enforce strict CPU, memory, process, file-size, and wall-clock limits.
- Run binaries as a dedicated unprivileged user with no extra capabilities.
- Mount only a temporary work directory; toolchain and sources are read-only.
- Apply seccomp/BPF or similar filters; disable networking and device access.
- Clear environment variables and block `LD_PRELOAD` or `ptrace` hooks.

### Build & Execution
- Compile with deterministic flags and sanitizers (ASan/UBSan) when enabled.
- Link only against whitelisted system libraries; prefer static linking.
- Hash binaries and treat them as ephemeral artifacts.
- Capture stdout/stderr with size caps and record exit status.
- Remove temporary files and mounts after execution completes.

### Monitoring & Response
- Log sandbox configuration and resource usage for each run.
- Abort and flag any policy violations or sanitizer failures.
- Version-control sandbox profiles to guarantee repeatability.

## Mitigations
- Prefer `isolate` as the default sandbox; fall back to `nsjail` or `runsc` if
  available.
- Keep host kernels and sandbox runtimes patched.
- Run integration tests using malicious samples (fork bomb, file read, network
  open) to verify containment.
- Audit logs for anomalies and block forbidden syscalls or paths.
- Adopt defense in depth: containerization, sandboxing, and unprivileged users.
