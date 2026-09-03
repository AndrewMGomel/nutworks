# Changelog

## Unreleased

## 0.2.0 — 2026-09-03 public prerelease

Nutworks 0.2.0 makes NUTS easier to trust on complex work. It avoids
unnecessary approval questions, stays focused on the work you authorized, and
reports honestly when work remains.

### What's better

- **Fewer unnecessary stops.** A Plan or reviewer cannot create an approval
  requirement on its own. NUTS keeps going when existing rules or your prior
  permission already settle the choice, and stops earlier when a real decision
  belongs to you.
- **A more honest finish line.** The final Summary reflects the work and
  verification that actually happened. A polished explanation cannot turn an
  incomplete run into a success.
- **Safer plans and loose ends.** When the requested result is a Plan, the run
  finishes only after the final reviewed Plan is saved somewhere authorized and
  verified. Important open issues and reusable lessons must be saved somewhere
  an established person or system will follow them up, or the run reports
  itself incomplete.
- **Stronger scope control.** Problems inside the agreed work stay actionable.
  A correction that changes the agreed goal goes back through planning, while
  useful but unrelated discoveries do not silently widen the task.
- **More dependable review evidence.** A rewritten or shortened review summary
  cannot count as the original reviewer result, so required review passes
  reflect the reviews that actually happened.
- **Clearer guidance for new users.** The README now explains installation,
  NUTS's workflow, evidence handling, and pilot limits in plainer language.

### Technical details

- Only an original validated reviewer return observed by the runner, or an
  exact byte-for-byte copy, can count toward a required review pass. Redacted,
  normalized, abbreviated, or otherwise rewritten versions are derived
  summaries and cannot establish, repair, replace, or invalidate a pass.
- Human approval gates now require an authoritative source, a material
  user-owned decision or risk change, proof that no established default already
  covers it, and a dependent step or claim. Invalid gates remain work for the
  runner; genuine gates stop at the earliest informed point.
- Terminal state is derived from current phase evidence, verification, worker
  state, Compound outcome, FLAG and debt reconciliation, and exact Plan
  readback when planning. Missing, stale, contradictory, or unknown evidence
  means incomplete; the Summary reports that result but cannot change it.
- The completion boundary keeps defects inside the agreed goal actionable,
  returns goal-changing corrections to Plan before mutation and through the
  required revalidation, removes or narrows unsupported agent-invented
  safeguards, and prevents adjacent work from expanding a successful run.
- Planning outputs use one authorized durable destination, exact reviewed
  bytes, revalidated identity and privacy, and exact-byte readback. Failed or
  uncertain writes remain incomplete without a silent retry or fallback.
- Adjacent issues stay outside the current completion claim or move through an
  existing authoritative owner. A material reusable-learning candidate must be
  safely written or forwarded to such an owner and verified by semantic
  readback; otherwise Compound is blocked. NUTS adds no automatic backlog
  writer or new custody subsystem.
- Sensitive open issues and learning candidates use the smallest private record
  that preserves the decision, with the least-sensitive outward reference.
  Raw chats, prompts, secrets, credentials, tokens, and unrelated host history
  are not copied into durable records.
- On a compatible host, an explicit NUTS invocation may create or bind exactly
  one scoped goal as a continuation aid, never as phase evidence. Ambiguous or
  unrelated goals remain untouched, and an uncertain goal effect prevents
  later goal mutation until authoritative state is recovered.
- Planning now checks important premises against the shipped or runtime object,
  names evidence that could disprove them, supports negative-existence claims
  with bounded inspection, and considers whether a smaller or no-build answer
  is sufficient.
- A late user-requested Plan change that would invalidate most completed work
  first discloses the revalidation cost and asks whether to proceed. This is
  separate from an agent inventing an approval gate.
- Mixed code-and-document reviews remain one whole-target pass, with the target
  kind assigned per reviewer. Verification guidance now requires observable
  failing paths, no-op controls, isolation, and cleanup evidence where false
  success is a risk.
- NUTS still creates no project-local run folder and does not automatically
  save its terminal Summary as a file. Temporary retention and cleanup remain
  controlled by the host and operating system.

### Validation and pilot limits

- The candidate passed 70 deterministic tests, exact 23-file runtime-package
  closure, provenance validation across six adapted destinations and eight
  frozen sources, and official Codex static plugin validation.
- This remains a pilot-unqualified prerelease. Those checks do not prove model
  behavior, installed-host routing, marketplace discovery, cross-host parity,
  broad compatibility, privacy isolation, or rollback.
- The NUTS skill validator and Claude's strict plugin and marketplace validators
  were not rerun for this candidate, and no 0.2.0 installed-host smoke is
  claimed.
- Nutworks is not listed in the official OpenAI or Anthropic plugin
  marketplaces, has no runtime Compound Engineering dependency, and provides
  best-effort pilot support. It does not install, update, repair, or configure
  Compound Engineering. Rollback is not supported during the pilot.

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
