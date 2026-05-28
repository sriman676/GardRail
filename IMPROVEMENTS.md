# GuardRail — Improvements, Features to Add, and Changes

This document lists recommended features to add, changes to remove or avoid, hardening and improvements, and options for the `evolution` auto-apply workflow. It also covers deployment considerations for running inside a controlled internal network vs. public SaaS.

---

## High-level goals
- Harden the product for production use (security, reliability, observability).
- Make self-evolution safe and auditable.
- Provide flexible deployment options (single-tenant internal, multi-tenant SaaS).

---

## Features to Add (priority ordered)
1. Authentication & Authorization
   - Add HTTP auth for dashboard and API decision endpoints (OAuth2 / JWT / API keys).
   - Implement RBAC: roles for `viewer`, `operator`, `admin`, and `auditor`.
2. Rule Store & Management UI
   - Move `INJECTION_PATTERNS` out of `core/injection_scanner.py` into a JSON/YAML/DB-backed rule store.
   - Provide UI for adding, testing, enabling/disabling rules and rule versions.
3. Safe Evolution Workflow
   - Generate recommended changes as patch files or PRs instead of editing source in-place.
   - Provide an approvals step and dry-run review mode.
4. Alerting Integrations
   - Add webhook sinks and integrations (Slack, Teams, PagerDuty, email).
5. Metrics & Monitoring
   - Export Prometheus metrics (scan counts, threat distribution, provider failures).
   - Add health and readiness endpoints.
6. Audit Integrity & Retention
   - Add encryption/HMAC for audit entries (optional) and retention/archival policies.
7. Per-Tenant Policy & Config
   - Support per-project/tenant thresholds and rule overrides (allowlists/denylists).
8. Adversarial Test Suite
   - Add adversarial/fuzz tests and CI checks to catch regressions when rules change.
9. Offline/Local Classifier
   - Add an optional lightweight local model or ensemble detector for low-latency classification.
10. Packaging & CI/CD
   - Add Dockerfile, GitHub Actions CI (tests and lint), and publishable package metadata.

---

## Changes to Remove / Avoid
- Remove runtime editing of source code (`core/injection_scanner.py`) by `evolution._apply_new_rules`.
- Avoid writing secrets to `.env` or printing credentials to stdout.
- Avoid ad-hoc `print()` diagnostics; use structured logging instead.

---

## Hardening & Improvements
- Replace direct `.env` updates with a `recommendations` artifact (JSON/patch) and optional PR creation.
- Add retries/backoff for external LLM calls and graceful degradation policies.
- Ensure consistent async support across APIs and agent call paths.
- Enforce input size limits, chunking, and per-IP/tenant rate limiting.
- Add structured JSON logging and correlate `session_id`/`scan_id` across logs.
- Add startup config validation and fail-fast warnings for misconfiguration.
- Improve test coverage for `GenericLLMClient` failover, `SandboxSimulator`, and `DriftDetector` logic.

---

## Evolution Auto-Apply Options (safety-focused)
When `evolution` produces recommendations, you can adopt one of the following modes:

1. Manual Review (Recommended Default)
   - `evolution` outputs `recommendations.json` and a patch file containing suggested regex rules and threshold changes.
   - Developer reviews and merges changes via normal code review/CI.
   - Pros: Safe, auditable, fits existing dev workflows.
   - Cons: Slower to apply.

2. PR Automation (Balanced, Recommended for internal deployments)
   - `evolution` creates a branch, commits the suggested changes (rules file, `.env` suggestions as non-secret), and opens a PR with tests and rationale.
   - Admin/operator approves & merges after review.
   - Pros: Fast, auditable, integrates with CI.
   - Cons: Requires repo creds for automation and stricter CI to avoid regressions.

3. Staged Auto-Apply (Hybrid, Best for trusted internal networks)
   - `evolution` auto-applies changes to a staging environment only (updates rule store DB or config service) and runs a battery of automated adversarial tests.
   - If tests pass, it can either create a PR for production or apply to production automatically based on a policy flag.
   - Pros: Fast feedback loop, safer than direct prod edits.
   - Cons: More complex implementation.

4. Direct Auto-Apply (Not Recommended for public SaaS)
   - `evolution` writes directly to `core/injection_scanner.py` and `.env` at runtime.
   - Pros: Immediate remediation.
   - Cons: High risk, brittle, breaks reproducibility and audit trails.

**Best practices:** Use PR Automation for internal/controlled environments and Staged Auto-Apply for teams that want faster iteration but maintain safety gates. Avoid Direct Auto-Apply in almost all cases.

---

## Deployment Considerations: Internal Network vs Public SaaS

1. Internal Controlled Network (trusted infra)
   - You can rely on internal auth (single sign-on, internal IAM) and narrow network access.
   - Recommended features:
     - PR Automation or Staged Auto-Apply
     - Internal-only webhooks and secure internal storage for audit DB
     - Integration with internal secrets manager for LLM keys
   - Lower overhead for multi-tenant isolation if single-tenant per deployment.

2. Public SaaS / Multi-tenant (untrusted external users)
   - Strong isolation, tenant-aware config, strict RBAC, and encryption at rest & in transit are required.
   - Recommended features:
     - Multi-tenant design with per-tenant rule stores and RBAC
     - Strict rate limiting, quotas, and circuit breakers per tenant
     - Tenant-scoped audit logs, encryption, and export controls
     - Admin approval required for any auto-applied evolution change
     - Legal/compliance features (data residency, retention policies)

**Which is best?**
- For enterprise adopters inside a corporate network, choose Internal Controlled Network with PR Automation or Staged Auto-Apply.
- For a public SaaS product, default to Manual Review + PR Automation (admin approval required) and disable any auto-apply to production.

---

## Recommended Implementation Steps (next actions)
1. Move `INJECTION_PATTERNS` into `config/injection_rules.json` and update the scanner to load rules dynamically.
2. Update `evolution` to emit `recommendations.json` and a patch file OR create a branch + PR instead of in-place edits.
3. Add basic API auth and RBAC for the alert decision endpoints.
4. Add CI tests for adversarial samples and `evolution` dry-run validations.
5. Add a lightweight metrics exporter and health endpoints.

---

## Questions
1. For `evolution`, do you prefer: (A) Manual review only, (B) PR Automation, or (C) Staged Auto-Apply (hybrid)?
2. Will GuardRail be primarily deployed inside an internal corporate network, or as a public SaaS product (or both)?

---

If you confirm preferences for `evolution` behavior and deployment target, I can implement one of the quick wins (move rules to `config/injection_rules.json` and update the loader, and/or change `evolution` to write recommendations and create a PR instead of editing files directly).

---

## User Selections & Tailored Recommendations (Applied)
- Evolution mode chosen: **Staged Auto-Apply (hybrid, C)** — produce recommendations, apply to staging rule store, run automated tests, then promote to production via PR or automated policy if staging passes.
- Deployment target: **Both** internal controlled network and public SaaS — recommendations below are tuned for a mixed deployment strategy.

### Additional / Adjusted Recommendations for Staged Auto-Apply + Both Deployments

- Multi-tenant rule stores: implement namespaced rule stores (DB-backed) so each tenant can have their own active rule set and staged rules. Allow global shared rules for platform-level protections.
- Canary & staged rollouts: apply evolved rules to a small percentage of traffic or to a staging tenant first, run adversarial tests and metric checks, then gradually increase rollout if no regressions.
- Feature flags & policy gates: gate auto-applied changes behind feature flags and admin approval gates for SaaS tenants; allow operators to opt-in to automatic promotions for trusted internal tenants.
- Per-tenant isolation: enforce strict per-tenant configs, rate limits, quotas, and separate audit storage or tenant IDs in the audit DB to avoid cross-tenant leakage.
- Approval workflow & audit trail: every evolution change should generate a changelog entry, test results, and an audit record; approvals for production should be required for SaaS tenants.
- Secrets & keys: integrate with secrets managers (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault) instead of using `.env` for production API keys.
- Rollback & safety nets: implement automatic rollback triggers (metric regressions, increased false positives) and keep previous rule-set versions for quick revert.
- Performance & latency: run evolved rules evaluation in-memory or cache compiled regexes; for high throughput provide an option to offload scanning to a sidecar or dedicated service.
- Compliance & data residency: for SaaS, support tenant-specific data residency and retention policies; for internal deployments, allow local-only audit DB storage.
- Governance & tenant controls: provide a tenant admin API to approve or opt-out of automated evolution promotions.
- Testing & CI: add automated evolution unit/integration tests that run for every suggested change; block promotion if tests fail.
- Observability & SLOs: define SLOs (scan latency, false-positive rate) and alerting thresholds; gate promotions if SLOs are violated.

### Small additions to previously recommended list
- Convert `evolution` to emit both `recommendations.json` and a `staging_patch` that updates the rule store (not source files). The system then runs a test harness and metrics checks automatically.
- Add a `rule_version` column to the audit DB to track which rule-set was active for each scan; this helps debugging regressions when new rules are promoted.
- Harden file-write operations: have `evolution` only write to a controlled config directory (e.g., `config/evolution_output/`) and never directly to code files.

---

If you'd like, I can implement the first step now: move `INJECTION_PATTERNS` into `config/injection_rules.json`, update `core/injection_scanner.py` to load the JSON-backed rules and add a `rule_version` marker to logged scans. That will prepare the codebase for staged evolution flows.