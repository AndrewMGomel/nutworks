# Changelog

## Unreleased

## 0.2.1 — Unreleased candidate

### Keep NUTS focused on required work

NUTS could treat a plausible extra safeguard as mandatory work, even when the
requested result did not need it. That could expand the task and prolong review
instead of getting the actual fix finished.

This patch strengthens the check before a finding changes the plan or code:

- Proposed work must have evidence that it is necessary and authorized by the
  task, governing rules, or required correctness.
- Bundled suggestions are considered separately, so a genuine fix does not
  bring unrelated safeguards along with it.
- Suggested fixes remain advice, not automatic permission to edit.
- Missing or conflicting evidence leaves the decision unresolved rather than
  inventing permission. Earlier decisions are reconsidered when their evidence
  changes.

Required fixes and genuine safety, privacy, and policy obligations remain
actionable. Review stays broad; unnecessary implementation work is narrowed.

### Evidence and limits

The source correction passed 73 automated tests, package and source-origin
checks, and the official Codex plugin validator. Independent correctness and
simplicity review and hostile regression checks also passed.
These checks support the source and package, not model reliability.

Two separate behavioral observations support narrower claims:

- **A complete Full run:** in one complete, source-bound Full run in a separate
  Codex test environment, all 23 selected runtime members matched the exact
  candidate. NUTS repaired a small CSV-report utility. It calculated valid totals and
  rejected duplicate or malformed records without overwriting an existing report.
  Six tests and three additional direct checks passed. Audits raised
  concerns about interrupted writes and memory use. NUTS recorded them as
  remaining concerns without making them requirements, and completed the work.
- **A controlled component test:** using the same behavioral NUTS instruction tree, the model
  knew it was being evaluated for qualification and was explicitly told to apply
  the rule for deciding whether a review suggestion becomes required work.
  A supplied proposal bundled a real date-range fix
  with an unsupported record limit or disk-spill requirement. NUTS applied the
  real fix and left the extra safeguard out. All three unchanged tests passed,
  including retention of 5,000 valid records. This was not a Full run or an
  unprompted reviewer discovery.

Two independent reviews accepted these limited interpretations. The
observations used different Codex builds and reasoning settings; they are not
one combined run or evidence of reliability across hosts or models.

The Full run's initial plan already excluded guarantees against interrupted
writes. No reviewer proposed making those guarantees mandatory. Its original
**INSUFFICIENT_COVERAGE** verdict under the stronger late-proposal criterion
therefore remains unchanged. The controlled test does not show that an
unsuspecting Full runner would reject a persuasive reviewer who wrongly called
an extra safeguard mandatory. Neither observation establishes that the original 64-pass review
problem is generally solved. Nutworks remains **pilot-unqualified**.

Earlier outcomes remain unchanged. A conflicting-retention-rules exercise left
the conflict unresolved and made no changes, but sandbox restrictions blocked
verification; it remains **INCONCLUSIVE**. A file-copy exercise fixed real defects
and passed 15 tests, but a blocked Git-index update left Full incomplete. Its
earlier capacity-limited launch stopped before model work. The draft-cockpit
replay lacked the required coverage; its amended attempt violated the offline
execution boundary and was rejected. None is upgraded by the later observations.

After the Full observation, the separate environment's exact `v0.2.0` predecessor
payload and selection were restored; candidate source and ambient package remained
unchanged. This does not establish general rollback support or complete host
isolation. Encrypted task assignments and additional host-supplied descriptions
prevented complete reconstruction of every child input. During the Full-run campaign
interval, the live configuration's reasoning setting changed from medium to low
with unknown attribution. Native records show the observed parent and children
continued at medium; exact preservation of live configuration bytes is not
claimed. Native isolated-fixture trust and log additions remain. No private test
data or host records are included in the package.

The behavior change is the correction merged in PR #13; the behavioral NUTS
instruction tree is unchanged since then. The full `0.2.1`
candidate also changes version metadata, documentation, and release-identity
tests; its two changed runtime-package descriptors contain version-only changes.
This README/CHANGELOG reconciliation changes public documentation only. It leaves
the already-prepared candidate package bytes and behavioral instructions unchanged
and does not alter historical verdicts. No new runtime dependency, workflow phase,
automated rollback, or migration is added. Version `0.2.0` remains the public pilot.

## 0.2.0 — 2026-09-03

The central change in Nutworks 0.2.0 fixes a problem in earlier NUTS versions:
a suggested safeguard could become a new requirement, then trigger more
safeguards and repeated review. NUTS now checks each concern against the result
you authorized. Problems that affect that result remain part of the work,
changes to the goal return to planning, and unrelated ideas stay outside the
current run. This release also stops plans and reviewers from inventing approval
requirements and reports “finished” only when the work and checks support it.

### What's better

- **Stops suggested safeguards from snowballing.** A safeguard is not required
  just because a plan or reviewer suggests it. NUTS first checks whether it
  follows from your request, governing rules, safety, or correctness needed for
  the requested result. Problems that affect that result remain work, changes
  to the goal return to planning, and unrelated ideas stay outside the current
  run.
- **Asks fewer unnecessary approval questions.** A plan or reviewer cannot
  require your approval on its own. NUTS continues when existing rules or your
  prior permission already settle the choice, and asks earlier when a real
  decision belongs to you.
- **Makes “finished” mean something.** The final summary is based on the work
  and verification that actually happened. A polished explanation cannot turn
  unfinished work into a success.
- **Keeps plans and important loose ends from disappearing.** When a plan is the
  requested result, NUTS saves and verifies the final reviewed plan. Important
  open issues and reusable lessons must be handed to an existing place or owner
  responsible for follow-up, or the run reports itself incomplete.
- **Counts the reviews that actually happened.** Rewritten summaries cannot
  count toward a required pass, so pass accounting stays tied to the validated
  reviewer return.

### Technical details

- The completion boundary keeps defects inside the agreed goal actionable,
  returns goal-changing corrections to Plan before mutation and through the
  required revalidation, removes or narrows unsupported agent-invented
  safeguards, and prevents adjacent work from expanding a successful run.
- Human approval gates now require an authoritative source, a material
  user-owned decision or risk change, a recorded reason no established default
  covers it, and a dependent step or claim. Invalid gates remain work for the
  runner; genuine gates stop at the earliest informed point.
- Terminal state is derived from current phase evidence, verification, worker
  state, Compound outcome, FLAG and debt reconciliation, and exact Plan
  readback when planning. Missing, stale, contradictory, or unknown evidence
  means incomplete; the Summary reports that result but cannot change it.
- When the requested result is a Plan, NUTS selects one authorized durable
  destination without asking a preference question, keeps the draft temporary
  through review, writes the exact reviewed bytes once, and reads them back. No
  safe destination blocks Critique; a failed or uncertain write leaves the run
  incomplete without retry or fallback.
- Adjacent issues stay outside the current completion claim or move through an
  existing authoritative owner. A material reusable-learning candidate must be
  safely written or forwarded to such an owner and verified by semantic
  readback; otherwise Compound is blocked. NUTS adds no automatic backlog
  writer or new custody subsystem.
- Only an original validated reviewer return observed by the runner, or an
  exact byte-for-byte copy, can count toward a required review pass. Redacted,
  normalized, abbreviated, or otherwise rewritten versions are derived
  summaries and cannot establish, repair, replace, or invalidate a pass.
- Sensitive open issues and learning candidates require minimum actionable
  private custody containing only a safe ID, state, next action, and closure
  condition, plus the least-sensitive outward reference to that same owner. Raw
  chats, prompts, credentials, tokens, environment dumps, and unrelated host
  history are excluded.
- On a compatible host, an explicit NUTS invocation may create or bind exactly
  one scoped goal as a continuation aid, never as phase evidence. Ambiguous or
  unrelated goals remain untouched, and an uncertain goal effect prevents
  later goal mutation until authoritative state is recovered.
- Planning must now check important premises against the shipped or runtime
  object, name evidence that could disprove them, support negative-existence
  claims with bounded inspection, and consider whether a smaller or no-build
  answer is sufficient.
- After Review begins, a user-requested load-bearing Plan change that would
  restart or revalidate most of the selected mode first discloses that cost and
  asks whether to proceed, unless the user already acknowledged it. This is
  separate from an agent inventing an approval gate.
- Mixed code-and-document reviews remain one whole-target pass, with the target
  kind assigned per reviewer. Verification guidance now requires observable
  failing paths, no-op controls, isolation, and cleanup evidence where false
  success is a risk.
- The README now explains installation, NUTS's workflow, evidence handling, and
  pilot limits in plainer language.
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
- Nutworks is not listed in the OpenAI-curated or Anthropic official plugin
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
