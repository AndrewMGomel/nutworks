# Plan Protocol

Use this protocol during NUTS's Plan phase. The main runner owns the plan and
all user interaction. Research contexts may return evidence, but they do not
settle scope, mutate the workspace, or claim implementation.

## The outcome

A great plan enables three audiences to act:

- **The implementing agent** starts from an informed baseline: load-bearing
  decisions are named, research breadcrumbs orient investigation, and unit
  boundaries are clear. The plan gives the implementer a starting point, not a
  substitute for checking the current workspace.
- **The reviewer** identifies the load-bearing decisions and the boundaries of
  what will change in one pass.
- **The future reader** can trace why the work was done, what shaped it, and
  where its artifacts live.

Sections earn their place by serving one of these audiences. Omit padding.

## Inputs and authority

Before writing the plan:

1. Read the applicable repository authority and the user's current request.
2. Inspect the current code, nearby patterns, declared truth locations, durable
   learnings, and real verification commands that bear on the task.
3. Carry forward settled decisions and explicit scope boundaries.
4. Identify product, policy, privacy, destructive-action, capability, or public
   mutation gates that the plan cannot decide on the user's behalf.
5. Distinguish verified facts from assumptions and unresolved questions.

For every load-bearing premise, record the object users actually run or
receive, the observation or command that could falsify the premise, and the
result. A negative existence claim such as “there is no X” requires the bounded
search or command behind it. Ask four framing questions before committing to
the approach: Are we inspecting the shipped/runtime object? What evidence could
disprove the premise? Is a smaller no-build answer sufficient? Do apparently
opposed fixes share a deeper cause? Apply this checkpoint to material premises,
not every minor assumption. Contradictory evidence changes the Plan before
Critique; unavailable evidence is an explicit gap and blocks only the claim
that depends on it.

Do not invent a path, command, integration, public identity, compatibility
promise, or repository convention. If a required fact cannot be discovered,
make its discovery or decision an explicit gate owned by the main runner.

## Session-settled decisions

Classify a conversation-carried decision by whether it survived examination,
not by how confidently it was stated:

- **Settled**: a tradeoff, alternative, or risk was surfaced and the user chose
  with it in view. Record it with one of the provenance classes below.
- **Directive**: the user asserted a choice that was not examined. Preserve it
  as authority, but do not mislabel it as settled; surface evidence that makes
  it infeasible, unsafe, destructive, or the wrong task.
- **Unlabeled**: the runner inferred or proposed it without user engagement.
  Treat it as ordinary planning input, never as a user decision.

Never self-settle an agent proposal or upgrade bare assent to a stronger class.
Use exactly these visible classes when a decision is settled:

- `user-directed`: the user chose against or between surfaced options.
- `user-approved`: the runner proposed an option with its tradeoff and the
  user assented.

Record a settled decision on the relevant decision entry in this form:

`(session-settled: user-directed — chosen over <alternative>: <reason>)`

The annotation must be understandable without the conversation. Never re-ask
a settled decision. Research may contradict it only with evidence. A merely
suboptimal but workable choice remains settled; evidence that makes it
infeasible, unsafe, destructive, or the wrong task becomes an explicit gate.
Settlement never suppresses a defect found inside the chosen approach.

## Implementation-ready floor

For a file-changing Full or Light NUTS run, the plan must include the following
content. Headings may follow the repository's conventions, but each contract
must be findable in one pass.

### Goal and authority

State the objective, success condition, authority order, constraints, scope,
stop conditions, and selected NUTS mode. Name what the plan does not authorize.

### Requirements and scope

State observable requirements with stable IDs when the work is large enough to
need traceability. Group requirements by concern when they span distinct
capabilities. Identify included work, excluded work, deferred work, actors, and
state-dependent acceptance examples when material.

### Planning decisions

Name the decisions that constrain implementation, their rationale, assumptions,
dependencies, failure modes, compatibility boundaries, reversibility, and any
high-level design that prose alone cannot carry. Preserve applicable
session-settled annotations.

### Implementation units

Divide the work into dependency-ordered units sized so each can be executed and
verified. Every unit names:

- its goal;
- the requirements it satisfies;
- concrete repository-relative files or an explicit path-discovery gate;
- its approach and mutation boundary;
- material happy, missing, empty, and error paths;
- test scenarios; and
- verification using the repository's real commands.

Use a compact unit index only when it materially improves navigation. The unit
bodies remain authoritative.

### Verification contract

Name the actual test, lint, build, validation, or inspection commands that
prove the work. State what each gate proves and does not prove. Where a command
or capability is unavailable, identify the resulting evidence gap instead of
substituting a plausible-looking command or claiming success.

### Definition of Done

Give global and per-unit completion criteria. Include cleanup of abandoned
attempts, current green evidence after fixes, accurate documentation and truth
surfaces, and any later action that remains separately authorized.

## Include when material

Include a section only when it carries information not already owned elsewhere:

- **High-level design** for architecture, sequencing, data flow, or branching
  gates that prose does not communicate cleanly.
- **Scope boundaries** when scope is contested or tempting non-goals need an
  explicit home.
- **Open questions** only for real blocking or explicitly deferred questions;
  never add an empty placeholder.
- **System-wide impact** for shared data, authorization, performance, agent,
  workspace, or infrastructure effects.
- **Risks and dependencies** for concrete external or implementation risks.
- **Acceptance examples** for conditional behavior whose edge cases are not
  obvious from the requirement.
- **Sources and research** when a breadcrumb will help an implementer make a
  better decision. Omit process exhaust.

Content drives section choices. Do not force information into an ill-fitting
template or add a section merely to make the document look complete.

## Failure-path and dependency check

For each new data flow, integration point, or state transition that is material
to the task, inspect:

- the expected path;
- missing or null input;
- present-but-empty input;
- upstream or command failure; and
- interruption, partial mutation, or rollback boundaries when the work makes
  those states possible.

Do not manufacture irrelevant edge cases. Include an edge only when it changes
the implementation, verification, or completion claim.

Every unit dependency must resolve to an earlier unit, an existing repository
capability, or a named external/manual gate. A plan is not implementation-ready
while a launch-blocking product or architecture question remains unanswered.
Deferred questions are allowed only when they do not block the planned work and
are labeled as deferred.

## ID and content rules

- Keep requirement, unit, actor, flow, acceptance-example, and decision IDs
  stable across revisions; never renumber merely to close gaps.
- Use repository-relative paths. If no safe relative path is known, write a
  discovery gate instead of an absolute or guessed path.
- Lead with the decision or outcome, then its reason and evidence.
- Keep one actionable idea per sentence where practical.
- Resolve superseded text in place. Do not stack a second resolution layer on
  top of contradictory text.
- Preserve concrete identifiers, thresholds, dates, paths, and commands when
  they are known.
- Separate requirement intent from implementation forks. Put unresolved forks
  in the proper decision or open-question section.

## Planning-only deliverables

When planning itself is the requested final deliverable, label the result
truthfully as one of:

- **Plan-as-Meta-Plan**: a plan for later planning or discovery;
- **Build-as-Plan**: an implementation-ready plan that another run will build;
  or
- **handoff**: bounded context and next actions for another owner.

Do not imply that code was implemented, shipped, released, or verified merely
because a plan exists.

When the Plan is the requested product, resolve its durable destination before
leaving Plan. An exact user-designated Plan destination wins when safe; source
paths, attachments, review targets, and incidental path mentions do not count.
Otherwise select the first eligible destination without asking a preference
question: the repository's declared Plan path, a specifically authorized
handoff path, an established nearby Plan directory, then a host-native durable
user-artifact location whose retention and exact readback are authoritative.
For an ordinary Plan, a declared Plan path precedes a handoff path. If no
candidate is eligible, report an early capability failure and do not dispatch
Critique. Never invent a repository root, `docs/NUTS/`, hidden run store, global
archive, or preference registry.

Keep the candidate in temporary evidence through Critique, Build-as-Plan,
Review, and the applicable Full audits. After convergence, revalidate the
selected parent, target identity, authority, privacy, and retention, then write
the exact reviewed bytes once through a byte-preserving path. Read the durable
target back and require exact byte equality. A failed, partial, mismatched, or
uncertain write is incomplete: preserve the observed effect, do not retry or
fall back, and do not treat the artifact's presence as completion. Before a
write, an automatically selected destination that becomes ineligible may move
to the next qualified candidate; rerun semantic clearance only when Plan bytes,
scope, or authority change. An invalid explicit destination never falls back.

Filesystem candidates require canonical no-follow checks of the complete
existing parent chain. For an absent target, exclusively create one new regular
file; a collision fails without overwrite. For an existing target, require
exact authority to mutate that logical Plan and reject links, special files,
and multiple hard links. An existing repository-owned Plan may use its
authorized editing path with either an identity-bound no-follow write or an
authorized atomic replacement whose new regular single-link identity is
captured and verified. An existing exact user-designated filesystem path
outside the repository requires an identity-bound no-follow write; atomic
replacement is not eligible there. Identity drift, an unauthorized overwrite,
or unavailable safe write primitive is incomplete. Repository writes also
require fresh single-writer evidence. Host artifacts must fail on
collision, remain intentionally retained and user-retrievable after the run,
expose a stable non-secret locator, and support exact-content readback. Unknown
privacy, sharing, or retention disqualifies a candidate. Do not copy chats,
credentials, host history, unrelated private paths, or temporary evidence into
the Plan. Summary-file durability remains a separate decision.

After every filesystem write or uncertain effect and before exact-byte
readback, revalidate the complete canonical parent chain, logical-path binding,
resulting target identity, regular-file/single-link/nonsymlink properties, and
destination privacy and access posture. Parent drift, target replacement, or
broader resulting access is incomplete and never permits retry or fallback.

During ordinary authority and task reads, retain any declared convention for
future issues, security obligations, or reusable learnings without inventorying
unused owner surfaces. Route later discovery, custody, precedence, and reviewed-
Plan gate eligibility to the sole detailed contract in
`evidence-and-claims.md`.

## Final checks

Before Plan can advance to Critique, confirm:

- settled decisions and explicit user constraints remain intact;
- no agent-invented behavior or authority entered the plan;
- every requirement maps to an implementation unit and proof;
- unit dependencies are acyclic and ordered;
- material failure paths and negative tests are present;
- paths and verification commands are current or gated for discovery;
- public, destructive, safety, privacy, and capability gates are visible;
- implementation claims are absent; and
- an implementer could begin without making an unrecorded architectural
  decision.
- a planning-only product has one eligible durable destination selected, with
  its exact-write and readback gates recorded; and
- material premises name the shipped/runtime object and falsifying evidence.
