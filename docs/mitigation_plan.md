# Mitigation Plan

This plan accompanies `risk_register.md` and describes how the team will address each identified risk.

## R1 – Sandbox escape leading to host compromise
- Use `isolate` with a strict seccomp profile.
- Include malicious sample tests in CI.
- Review sandbox configuration changes.

## R2 – Missing toolchain components delaying development
- Ship `env_probe.py` to verify required tools on the host.
- Document required packages and fail fast when tools are absent.

## R3 – Dataset licensing conflicts
- Maintain a dataset catalog with license information and source URLs.
- Require manual license review for new datasets.

## R4 – Loss of determinism in builds or tests
- Pin toolchain versions, seeds, locale, and time zone.
- Add determinism checks to CI pipelines.

## R5 – Sandbox misconfiguration causing resource exhaustion
- Run stress tests and enforce CPU/memory limits for each run.

## R6 – Supply chain compromise of toolchain or dependencies
- Pin dependency versions, verify checksums, and maintain a software bill of materials.

## R7 – Dataset contamination or sensitive data leakage
- Scan datasets for PII and track provenance before inclusion.

## R8 – Logs or artifacts leaking credentials or PII
- Scrub logs and restrict retention of artifacts containing runtime output.

This plan will evolve as additional risks are discovered.
