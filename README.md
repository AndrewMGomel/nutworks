# Nutworks

[![Compound Engineering](https://img.shields.io/badge/Built_with-Compound_Engineering-6366f1)](https://github.com/EveryInc/compound-engineering-plugin)
[![Built with NUTS](https://img.shields.io/badge/Built_with-NUTS-2f855a)](https://github.com/AndrewMGomel/nutworks)

Nutworks is a native plugin package whose first skill is NUTS, a rigorous
engineering workflow for planning, implementation, review, audit, learning,
and evidence-backed closeout.

This public `0.1.0` prerelease is **pilot-unqualified**. Its deterministic
package and workflow contracts are tested, and ordinary native installation
has been smoke-tested on the exact builds listed below. Clean standalone
semantics, cross-host parity, and broad Codex or Claude support have not been
qualified. Nutworks is distributed from its
[GitHub repository](https://github.com/AndrewMGomel/nutworks); it has not been
submitted to an official plugin directory.

Nutworks has no runtime Compound Engineering dependency. It never installs,
updates, repairs, or configures CE.

## Install the `0.1.0` pilot

### Codex

```bash
codex plugin marketplace add AndrewMGomel/nutworks --ref v0.1.0
codex plugin add nutworks@nutworks
```

Start a fresh task and invoke `$nuts`.

### Claude Code

```bash
claude plugin marketplace add AndrewMGomel/nutworks@v0.1.0 --scope user
claude plugin install nutworks@nutworks --scope user
```

Start a fresh session and invoke `/nutworks:nuts`.

Native installation does not copy NUTS into `AGENTS.md`, `CLAUDE.md`, or other
project governance. A NUTS run creates no project-local evidence directory by
default. When the host already permits a verified owner-private system-
temporary directory without new approval or configuration, NUTS may use one
temporary working sidecar outside the selected project and plugin source;
otherwise it keeps evidence in the host conversation. At terminal closeout it
emits one self-contained conversation Summary. Temporary cleanup and transcript
retention remain host-controlled.

Keeping default working evidence outside the selected project prevents NUTS's
own files from entering that project's ordinary Git status or project-root
Docker/build context. This is not a confidentiality, durability, deletion-time,
or unrelated parent-build-context guarantee. NUTS never edits Git, Docker,
package, cloud, or deployment ignore/configuration files for evidence storage.

The pilot user only installs and uses the skill. They are not being asked to
run a test plan, collect diagnostics, upload evidence, or repair plugin state.

## Development installation

Maintainers working from a local checkout may substitute its absolute path for
`AndrewMGomel/nutworks` in the marketplace-add command. Local installation is
for development; the `v0.1.0` tag is the immutable public pilot identity.

## Maintainer verification

Run the normal deterministic suite:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_package.py
python3 scripts/validate_provenance.py
```

Run the official Codex validator in a maintainer environment with the pinned
development dependency:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.lock
.venv/bin/python scripts/validate_official_codex.py
```

The current candidate passed its deterministic test suite, source/stage closure,
provenance validation, the official Codex plugin validator, the NUTS skill
validator, and Claude's strict plugin and marketplace validators. Ordinary
install/list smoke passed on `codex-cli 0.147.0-alpha.6.5` and Claude Code
`2.1.214`; those observations apply only to those exact builds and disposable
plugin-state roots. They do not prove privacy isolation, model behavior,
semantic parity, cache custody, rollback, or general host support.

Rollback is not supported in this pilot. Removal uses the host's native plugin
management rather than a Nutworks migration or repair path.

## Feedback and support

[GitHub Issues](https://github.com/AndrewMGomel/nutworks/issues) are enabled for
bug reports and pilot feedback. Support is best-effort, with no compatibility,
response-time, or resolution guarantee during the pilot.

## License

Nutworks's original material is MIT licensed, copyright 2026 Andrew Gomel.
Identified Compound Engineering-derived material retains Every's separate MIT
notice and provenance in `plugins/nutworks/THIRD_PARTY_NOTICES.md`.
