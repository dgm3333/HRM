# Risk Register

This register tracks early risks for Phase 0 of HRM Coder and proposed mitigations.

| ID | Risk | Impact | Likelihood | Mitigation |
|----|------|--------|------------|------------|
| R1 | Sandbox escape leading to host compromise | High | Medium | Use `isolate` with strict seccomp and run integration tests with malicious code |
| R2 | Missing toolchain components delaying development | Medium | Medium | Provide `env_probe.py` utility and document required packages |
| R3 | Dataset licensing conflicts | High | Low | Maintain dataset catalog with source URLs and license details |
| R4 | Loss of determinism in builds or tests | Medium | Medium | Pin toolchain versions and enforce fixed seeds |

This document will be updated as new risks are identified.
