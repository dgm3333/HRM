# Risk Register

This register tracks early risks for Phase 0 of HRM Coder and proposed mitigations.

| ID | Risk | Impact | Likelihood | Mitigation |
|----|------|--------|------------|------------|
| R1 | Sandbox escape leading to host compromise | High | Medium | Use `isolate` with strict seccomp and run integration tests with malicious code |
| R2 | Missing toolchain components delaying development | Medium | Medium | Provide `env_probe.py` utility and document required packages |
| R3 | Dataset licensing conflicts | High | Low | Maintain dataset catalog with source URLs and license details |
| R4 | Loss of determinism in builds or tests | Medium | Medium | Pin toolchain versions and enforce fixed seeds |
| R5 | Sandbox misconfiguration causing resource exhaustion | Medium | Medium | Include stress tests and enforce CPU/memory limits |
| R6 | Supply chain compromise of toolchain or dependencies | High | Low | Pin versions, verify checksums, and maintain SBOM |
| R7 | Dataset contamination or sensitive data leakage | High | Low | Scan sources, track provenance, and perform manual reviews |
| R8 | Logs or artifacts leaking credentials or PII | Medium | Low | Scrub logs and restrict artifact retention |

See [mitigation_plan.md](mitigation_plan.md) for detailed mitigation actions for each risk.

This document will be updated as new risks are identified.
