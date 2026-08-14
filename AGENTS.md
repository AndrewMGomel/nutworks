# Nutworks Repository Contract

This repository builds the Nutworks native plugin package. NUTS is its first
skill.

## Scope

- Keep one behavioral source at `plugins/nutworks/skills/nuts/`.
- Keep Codex and Claude packaging as thin native metadata around that source.
- Do not add a runtime Compound Engineering dependency or CE management.
- Do not copy these repository instructions into projects that install NUTS.
- Treat every push, PR, merge, release, directory submission, or other
  publication as a separately authorized operation. Public availability never
  grants standing authority for later publication.
- Keep the first candidate labeled pilot-unqualified. Cross-host semantic
  qualification is deferred.
- Never copy private development evidence, absolute private paths, raw chats,
  host history, credentials, or recipient data into this repository or the
  installable payload.

## Implementation Discipline

- Prefer the smallest change that satisfies the current requirement.
- NUTS runtime behavior must trace to the approved behavioral lineage; do not
  add workflow semantics because they seem useful.
- Preserve the v0.1 F1 cut: no custom journal/checkpoint engine, active-run
  marker, lease, replay/recovery/resume/migration system, worker fencing,
  cleanup-pending state, pass/runtime ceiling, or custom terminal-state engine.
- Use `apply_patch` for manual file edits.
- Preserve CE-derived wording and structure when compatible. Record every
  material adaptation and retain Every's MIT notice.

## Verification

Run the normal suite from the repository root:

```bash
python3 -m unittest discover -s tests -v
```

Also validate the skill and Codex plugin using the documented maintainer
commands in `README.md`. Host smoke is focused, disposable, and never mutates a
live profile.
