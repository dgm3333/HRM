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

## Mitigation Plan

- **R1:** Harden sandbox profiles, apply strict seccomp, and run malicious sample tests in CI.
- **R2:** Distribute `env_probe.py` and document required packages in README; fail fast when tools are missing.
- **R3:** Keep dataset catalog with licenses and URLs; require contributors to record provenance.
- **R4:** Pin toolchain versions, seeds, locale, and time zone; add deterministic build checks.
- **R5:** Add stress tests for CPU and memory limits; monitor resource usage within sandbox.
- **R6:** Pin dependency versions, verify checksums, and maintain a software bill of materials.
- **R7:** Scan datasets for PII or license conflicts and review sources before inclusion.
- **R8:** Scrub secrets from logs and limit access to artifacts containing runtime output.

This document will be updated as new risks are identified.
