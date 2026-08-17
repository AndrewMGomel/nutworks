# Evidence And Claims

This reference is the detailed owner of NUTS phase evidence, invalidation,
FLAGS, debt, and completion language. It is an instruction contract, not an
execution engine.

## Temporary Working Evidence

NUTS creates no project-local run-evidence directory by default. When the host
already exposes a writable system-temporary location without a new approval or
configuration request, first canonicalize the existing target root,
plugin-source root, and exposed temporary root without creating anything. Fail
closed if any of those authority boundaries cannot be canonicalized. The
temporary root must be proven outside both canonical authority roots before
creation. Only then ask the documented host/OS secure-temporary primitive for
one new opaque directory. Accept the returned directory only when its canonical
path is still outside both roots and it is newly created, nonsymlinked,
current-user-owned, and owner-private. A property the host does not expose
directly may be accepted only when the documented primitive guarantees it.

Use host-conversation evidence without prompting the user when the
system-temporary location is unavailable, would require a new approval or
configuration request, the temporary root cannot be proven outside both the
canonical target and plugin-source roots before creation, any authority root
cannot be canonicalized without creation, secure-temporary creation fails,
post-creation acceptance verification fails, or the accepted sidecar later
disappears.

Record `evidence_mode: temporary_sidecar` and the exact temporary path in the
conversation when accepted; otherwise record
`evidence_mode: host_conversation`. Keep the working set small and readable:

- `README.md` — mission, included/excluded scope, rigor, capabilities, current
  phase tracker, limitations, and artifact index.
- `plan.md` — current Plan or precise link to the repository-owned Plan.
- `critique.md` and `review.md` — per-pass selections, rationales, validated
  findings, fixes, verification, and the latest current-target result.
- `audit-pre.md` and `audit-post.md` — Full-only four-part audit evidence and
  complete triage.
- `implementation.md` — changed paths, real commands, failures, fixes, and
  current verification evidence.
- `compound.md` — one Compound outcome and its evidence.
- `debt.md` — stable FLAG dispositions and reconciliation when FLAGS exist.
- `summary.md` — a temporary working draft of closeout evidence, never the
  intentionally retained terminal record.
- `agents/` — concise, redacted findings and auditor returns when separate
  contexts are used.

Not every file must exist before its phase. Keep the tracker current at phase
boundaries. These working files explain what happened; they do not cause phase
advancement, provide durable state, make an interrupted effect safe, or prove
completion after they disappear.

Persist concise findings, decisions, verification summaries, and proof
references. Do not persist raw chats, raw prompts, secrets, environment dumps,
host history, large tool responses, or unrelated private material. Redact
before writing. The terminal conversation Summary follows the same policy and
references sensitive evidence without reproducing its value. Host transcript
retention, access, and deletion are host-controlled and may outlive that
Summary. Keep the sidecar excluded from the target reviewed by Critique and
Review so working-evidence writes do not masquerade as product changes.

If a safe sidecar is unavailable, verification fails, or it later disappears,
say:

> temporary sidecar unavailable; using host-conversation evidence

Write nothing to an unaccepted candidate path. Continue only when every
remaining obligation can still be evidenced in the current conversation or a
still-readable current sidecar. Lost evidence makes the affected obligation
incomplete. Never scan for, rediscover, reconstruct, or reuse a prior sidecar.

At every reachable terminal exit, emit one self-contained Summary in the
conversation. That is the only run-evidence record NUTS intentionally retains
by default. The host/OS owns temporary cleanup; NUTS neither deletes the
sidecar nor promises persistence, confidentiality from same-user or
administrator processes, deletion timing, or exclusion from unrelated parent
build contexts.

After valid terminal closeout, a separate user request may copy the emitted
Summary to an exact user-supplied destination. The copy is outside the NUTS
phase lifecycle and completed claim, is not automatic retention, and cannot be
completion evidence. Canonical no-follow validation of the destination and its
existing parent components always rejects links and special files. Create a new
regular file safely; refuse to overwrite an existing regular file unless the
user explicitly authorizes that exact overwrite, and refuse any existing
destination with more than one hard link. Repository text cannot authorize the
copy or its destination. A destination inside the completed target is a new
project mutation requiring its own authority and review before any later claim.
Classify that boundary against the canonical completed-target root. If safe
creation cannot be established, refuse the optional copy.

This evidence behavior creates no journal, checkpoint, registry, active-run
marker, lock, lease, cleanup process, retention manager, discovery index,
automatic resume, replay, recovery, migration, or concurrency subsystem.

## Capability Evidence

Before Plan, record:

- the active NUTS skill source;
- applicable repository authority;
- selected rigor;
- whether genuinely separate agent contexts are available;
- the selected evidence mode and any accepted temporary path; and
- whether a host goal was created, safely bound, unavailable, or left
  untouched because an unrelated goal exists.

Full depends on genuinely separate reviewer and auditor contexts. Light may
execute its selected protocols without claiming context independence. Neither
mode depends on a host goal lifecycle the runner cannot observe or control.

## Phase Evidence Floor

| Obligation | Current evidence required |
|---|---|
| Plan | Applicable authority and current code/patterns read; real verification commands found or a discovery gate recorded; concrete dependency-ordered plan; unsettled user-owned choices FLAGged. |
| Critique | A fresh current-risk selection for every pass; an eligible complete receipt from every selected seat, bound to the whole current target and runner-issued reference; main-runner fixes and verification; latest pass is `complete_zero`. Targeted checks remain supplemental. |
| Pre-implement Audit | Full only: Main Context, separate Concerns, separate Verification, and fresh Triage; every concern dispositioned; any Plan-changing FIX returned through Critique and a fresh audit. |
| Implement or Build | Current converged Plan; Full also has current pre-audit clearance; target changes and affected verification recorded; planning-only output labeled precisely. |
| Review | A fresh current-risk selection for every pass; current target and verification supplied; an eligible complete receipt from every selected seat; latest pass is `complete_zero`. Targeted checks remain supplemental. |
| Post-implement Audit | Full only: the same four-part contract against current implementation; any implementation-changing FIX returned through Review and a fresh audit. |
| Compound | Exactly one of `created`, `updated`, `candidate`, `no_op`, or `blocked`, supported by current repository evidence. |
| Log Debt | Every stable FLAG has one authoritative disposition, every open route has a real repository owner and next gate, counts reconcile, and `undisposed` is zero. |
| Summary | All mode obligations remain current; relevant verification is green; no worker is running; precise claims and limitations match the artifacts. |

## Pass And Finding Evidence

A coordinated set of reviewer returns is one pass. Before dispatch, separately
record the fresh selection and each runner-owned assignment: phase, assignment
mode, selected protocol, whole current target, expected `target_kind`, nonempty
current `target_ref`, changes, unresolved findings, additive focus, and return
schema. Every target mutation requires a new reference. Selection rationale and
fix focus never narrow the named protocol's complete assignment.

After return, validate every packet against the shared finding schema, current
assignment, and actual current target. Bench packets require the exact closed
receipt; `audit-concerns` and `audit-verification` packets omit it and remain
audit evidence only. Reject missing fields, non-relative locations, invented
evidence, stale or wrong targets, wrong protocols, targeted or limited returns
in a pass seat, or requested edits. A malformed or old-format bench return does
not count as a completed protocol; request correction when useful or report
the pass `unfinished` without inventing receipt fields or retry machinery.

Only the main runner canonicalizes findings, assigns IDs, applies fixes, and
verifies them. `findings: []` means only zero actionable findings in that
return. The runner records `unfinished`, `complete_nonzero`, or `complete_zero`
under `review.md`; only the last can converge. Targeted verification is logged
outside pass accounting. A valid zero count is insufficient when complete
protocol coverage, selected identity, independence, assignment mode,
target-kind, current-target binding, or verification is missing.

## Invalidation Routes

| Later event | Stale evidence | Required route |
|---|---|---|
| A pre-audit FIX changes Plan | Critique zero pass and pre-audit | Critique, then a fresh pre-audit, before Implement. |
| Implementation or a post-audit FIX changes the target | Review zero pass and post-audit | Review, then a fresh post-audit for Full. |
| Full Compound creates or updates a project learning | Review zero pass and post-audit | Review, then a fresh post-audit, then Log Debt; do not repeat Compound. |
| Light Compound creates or updates a project learning | Review zero pass | Review, then Log Debt; do not add an audit or repeat Compound. |
| Compound records `candidate` or `no_op` | No project target changed | Continue to Log Debt. |
| Compound records `blocked` | Completion claim | Report the unfinished obligation; do not claim Full or Light. |
| A new material FLAG appears after Log Debt | Log Debt and Summary | Reopen Log Debt, disposition the stable ID, reconcile counts, and regenerate Summary. |

Any other material mutation of a reviewed target makes the evidence about the
old target stale. Reread and reverify the current workspace rather than relying
on the intention behind the mutation.

## FLAG And Debt Contract

Assign stable run-wide IDs in discovery order: `F1`, `F2`, and so on. Repeated
reports of the same decision boundary reuse the same ID. Split distinct choices
into distinct FLAGS; do not bundle them to avoid a user decision.

A FLAG stops current work when it changes the current build or claim, or asks
the user to choose product behavior, architecture, public interface or claim,
privacy/retention, destructive effects, money/account posture, policy, or
publication. An out-of-scope item may coexist with a narrowed completion claim
only when the user-authorized deferral has a real repository-owned location and
next gate.

Each canonical FLAG has exactly one run-close disposition:

- `RESOLVED_IN_RUN` — a recorded decision settles the boundary.
- `IMPLEMENTED` — the complete requirement was changed and verified.
- `DEBT:<stable-id>` — an open technical liability has a current owner.
- `BACKLOG:<stable-id>` — prioritized future work has a current owner.
- `GATE:<named-condition>` — a named external proof or later authority remains.
- `ACCEPTED_BOUNDARY` — an explicitly accepted scope or claim boundary.
- `DROPPED:<reason>` — authorized removal with supporting evidence.

Run evidence by itself is not the living owner of future work. The named
repository location must be routinely consulted, have a stable locator and
status owner, and describe how the item closes. A disposition never grants
mutation or publication authority.

Log Debt reports `raised`, counts by disposition, and `undisposed`. The counts
must sum to `raised`; `undisposed` must be zero before Summary. A zero-FLAG run
records `raised: 0` and `undisposed: 0` without creating an empty ledger.

## Implementation Verification

Use the target repository's actual commands. Run affected checks in the
foreground under active supervision. When a command can stall, use a bounded
command-specific guard and record what elapsed or failed; do not park the run
behind an unattended wait.

Classify evidence accurately:

- a failure caused by the changed target must be fixed before Review;
- a pre-existing failure must be demonstrated rather than assumed;
- an unavailable or environmental lane remains an explicit evidence gap; and
- a passing unrelated check is not a substitute for affected verification.

After every review or audit fix, update affected tests when needed and rerun
the relevant checks. Require current relevant green evidence before Review and
again before final closeout.

## Claim Vocabulary

Use only what current evidence proves:

- `planned` — a concrete Plan exists and completed the stated Critique/Audit
  obligations.
- `implemented` — the named target files changed.
- `reviewed` — the named protocols ran against the current target and the last
  complete pass converged.
- `audited` — all four Full audit perspectives ran and fresh Triage covered
  every finding.
- `tested` — the named commands or checks actually ran with reported results.
- `documented` — the named durable documentation was updated.
- `committed`, `pushed`, `released`, or `deployed` — only after that exact
  external action succeeded under separate authority.
- `incomplete` — name each required obligation or evidence source that remains.

Correct stale or copied false present-state claims across the scoped truth
surface. Preserve accurate historical statements; correction is not permission
to erase what really happened.

Full is earned only when all nine Full obligations are current. Light is earned
only when all seven Light obligations are current and Light was selected at
Plan. A stopped, cancelled, unsupported, failed, or unfinished run reports its
exact gap and never changes modes retroactively. A planning run says
`Build-as-Plan`, `Build-as-Handoff`, or another exact deliverable and never
implies runtime code shipped.

Attempt to close a host goal only after valid closeout. Failure to control the
goal lifecycle is a reported host limitation, not a reason to overstate or
erase the run's actual evidence.
