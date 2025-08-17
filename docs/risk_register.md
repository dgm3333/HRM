# Risk Register

This register tracks early risks for Phase 0 of HRM Coder and proposed mitigations.

| ID | Risk | Impact | Likelihood | Mitigation | Status |
|----|------|--------|------------|------------|--------|
| R1 | Sandbox escape leading to host compromise | High | Medium | Use `isolate` with strict seccomp and run integration tests with malicious code | Open |
| R2 | Missing toolchain components delaying development | Medium | Medium | Provide `env_probe.py` utility and document required packages | Mitigating |
| R3 | Dataset licensing conflicts | High | Low | Maintain dataset catalog with source URLs and license details | Open |
| R4 | Loss of determinism in builds or tests | Medium | Medium | Pin toolchain versions and enforce fixed seeds | Open |
| R5 | Experiment tracker exposes credentials or metrics | Medium | Low | Restrict access, require auth, run tracker behind VPN | Planned |
| R6 | GUI stack vulnerable to XSS or CSRF | Medium | Low | Use server-side templating, validate inputs, enable CSRF tokens | Planned |
| R7 | Unpatched dependency vulnerabilities in runner images | High | Medium | Maintain SBOM and rebuild images with security updates | Planned |

## Mitigation Plan

- **R1**: add CI security tests using known escape techniques; review isolate profiles quarterly.
- **R2**: keep `env_probe.py` as a pre-flight check in developer setup guides.
- **R3**: verify licenses before adding datasets and track provenance in `dataset_catalog.json`.
- **R4**: lock compiler versions in Dockerfiles and record `gcc --version` in run logs.
- **R5**: configure MLflow with per-user tokens and restrict network exposure.
- **R6**: adopt content-security policies and run dynamic analysis with OWASP ZAP.
- **R7**: enable Dependabot alerts and monthly base-image rebuilds.

This document will be updated as new risks are identified.
