# Compound

Compound asks whether the completed work produced one durable, reusable lesson.
It does not summarize the entire run, inspect host history, or create a learning
convention merely because this phase exists.

## Inspect

Use the current Plan, implementation, verification, Review, applicable audit,
and repository authority. Identify the repository's declared truth locations
and search only relevant existing learnings for overlap. Verify claims against
the current tree, including referenced paths, names, commands, counts, links,
and ownership.

Do not invent `docs/solutions/`, a glossary, or another truth owner. Do not read
raw conversations, unrelated run history, or private host data to manufacture a
lesson.

## Decide One Outcome

- `created` — one warranted reusable learning was added to an existing declared
  truth location.
- `updated` — one existing learning was corrected or extended because it
  overlaps the current lesson.
- `candidate` — a durable lesson appears warranted, but the repository has no
  safe declared destination or a later decision is needed; preserve it only in
  the current bounded working evidence or host conversation.
- `no_op` — no durable lesson exists beyond the current Plan, code, tests, or
  ordinary documentation.
- `blocked` — the phase cannot be completed honestly because required evidence
  is unavailable, unsafe, or contradictory.

Write at most one project learning. Prefer updating an overlapping learning to
creating a duplicate. `candidate` is not permission to add a new repository
convention. `blocked` makes the run incomplete and cannot support Full or Light.

## Ground The Result

For `created` or `updated`:

1. State the reusable problem and the evidence that makes it durable.
2. Keep claims scoped to the current repository evidence.
3. Revalidate every changed path, command, link, count, and present-tense claim.
4. Attribute outside material when applicable.
5. Record the one project path changed.

For every outcome, record what was inspected, why the outcome was chosen, what
was written, and any limitation.

## Revalidate Project Writes

A `created` or `updated` outcome changes the reviewed project target. Full must
return through Review and a fresh post-audit before Log Debt. Light must return
through Review before Log Debt. Do not repeat Compound after that verification
loop. A `candidate` or `no_op` changes no project target and proceeds directly
to Log Debt.

Compound does not push, publish, move unrelated files, or perform debt work.
