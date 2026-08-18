# Changelog

## Unreleased

- Distinguish authoritative reviewer returns from rewritten evidence summaries:
  only an original validated packet or its exact copy can affect pass
  accounting, while derived summaries must be labeled ineligible.
- Add regression coverage proving that a packet-like derived summary cannot
  fill a pass seat or invalidate a valid original return.

## 0.1.1 — 2026-08-17 public prerelease

- Correct Critique and Review pass accounting so only complete selected
  protocols against the whole current target can converge; targeted fix checks
  remain supplemental evidence.
- Add bench-only assignment receipts, preserve receipt-free Concerns and
  Verification audit packets, and bind pass eligibility to the runner's current
  protocol, target kind, target reference, and independence requirement.
- Add symmetric Critique/Review fixtures and structural schema/oracle parity
  checks without claiming independent Draft-7 execution or hidden reviewer
  diligence.

## 0.1.0 — 2026-08-14 public prerelease

- Add the first native Nutworks plugin package for Codex and Claude.
- Add NUTS as the first shared skill, with Full and Light workflows, fresh
  risk-based reviewer selection, two Full audits, Compound, debt reconciliation,
  and evidence-backed Summary.
- Add a bounded reviewer bench, including the risk-selected simplicity persona.
- Add deterministic workflow, package, privacy-closure, and provenance tests.
- Keep working evidence out of recipient projects by default with one
  best-effort verified temporary sidecar, conversation fallback, and one
  self-contained terminal conversation Summary; add no storage or cleanup
  subsystem.
- Preserve Every's MIT notice and exact provenance for the six destinations
  adapted from eight Compound Engineering 3.20.0 sources.
- Verify ordinary local install/list behavior on exact Codex and Claude builds
  without claiming model semantics or cross-host qualification.
- Publish the candidate as pilot-unqualified pending later isolated host
  goldens and broad cross-host qualification.
