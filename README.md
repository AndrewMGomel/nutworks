# Nutworks

[![Compound Engineering](https://img.shields.io/badge/Built_with-Compound_Engineering-6366f1)](https://github.com/EveryInc/compound-engineering-plugin)
[![Built with NUTS](https://img.shields.io/badge/Built_with-NUTS-8B5E3C)](https://github.com/AndrewMGomel/nutworks)

## Make your coding agent prove the work

Most coding agents can produce an answer. NUTS makes them defend it.

Nutworks is the plugin package. NUTS is its first skill: a rigorous workflow
for complex work with AI coding agents.

It stops “done” from meaning “the first answer looked plausible.” Instead,
NUTS guides your agent through a complete engineering loop:

1. **Plan** the work before changing anything.
2. **Challenge** the plan by asking reviewers to question its assumptions.
3. **Build** after reviewers have challenged the plan.
4. **Review** the whole result from multiple angles.
5. **Verify** the result with real evidence.
6. **Learn** from the work and report what remains.

Use NUTS when a task is too important for one confident first pass.

It helps your agent:

- put pressure on assumptions before implementation;
- find risks that the original builder missed;
- rerun reviews after meaningful changes;
- back completion claims with tests and evidence; and
- stop when a decision truly belongs to you.

Choose **Light** for focused work needing serious review. Choose **Full** for
broad, risky, or high-stakes work needing independent reviews and audits.

## Install NUTS

Version `0.1.1` is the current public pilot.

### Codex

If an earlier Nutworks pilot is installed, remove it first:

```bash
codex plugin marketplace remove nutworks
```

Then install `0.1.1`:

```bash
codex plugin marketplace add AndrewMGomel/nutworks --ref v0.1.1
codex plugin add nutworks@nutworks
```

Start a fresh task and invoke `$nutworks:nuts`. For example:

```text
Use $nutworks:nuts in Light mode to build [your task].
```

For bigger work, replace `Light` with `Full`.

### Claude Code

If an earlier Nutworks pilot is installed, remove it first:

```bash
claude plugin marketplace remove nutworks
```

Then install `0.1.1`:

```bash
claude plugin marketplace add AndrewMGomel/nutworks@v0.1.1 --scope user
claude plugin install nutworks@nutworks --scope user
```

Start a fresh session and invoke `/nutworks:nuts`. For example:

```text
Use /nutworks:nuts in Light mode to build [your task].
```

For bigger work, replace `Light` with `Full`.

## What “public pilot” means

This release is **pilot-unqualified**: tested, but not proven on every host build.

The package and workflow contracts have passed their documented tests.
Nutworks has not been qualified across every Codex and Claude build.

Nutworks is available from its
[GitHub repository](https://github.com/AndrewMGomel/nutworks). It is not listed
in the OpenAI-curated or Anthropic official plugin marketplaces.

Nutworks has no runtime Compound Engineering dependency. It never installs,
updates, repairs, or configures Compound Engineering.

## What NUTS leaves behind

Installing NUTS does not copy it into `AGENTS.md`, `CLAUDE.md`, or other
project instructions.

A NUTS run creates no project-local evidence folder by default.
It keeps working evidence in your agent conversation.
If your host allows it, NUTS may use a temporary working sidecar.
That folder sits outside your project and the plugin source.

This keeps NUTS files out of your project's normal Git status and project-root
build context. It does not guarantee confidentiality, durability, deletion
timing, or exclusion from a parent build context.
Your host still controls temporary cleanup and transcript retention.

NUTS requires one self-contained Summary at the end.
During this pilot, check that it gives you enough context.

NUTS never changes ignore files or project configuration to store evidence.
As a user, you install and invoke NUTS. The tests below are for maintainers.

## Development installation

Maintainers working from a local checkout may substitute its absolute path for
`AndrewMGomel/nutworks` in the marketplace-add command. Local installation is
for development; tagged releases remain immutable public pilot identities.

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

The published `v0.1.1` release candidate passed its deterministic test suite,
source/stage closure, provenance validation, and the official Codex plugin
validator. Those receipts apply to the published tag, not to later working-tree
changes. The current unreleased evidence-provenance correction has separately
passed the same deterministic, package, provenance, and official Codex
validation lanes. The pinned `PyYAML==6.0.2` dependency is maintainer-only
validation tooling; it is not a Nutworks runtime or end-user installation
dependency. The NUTS skill validator and Claude's strict plugin and marketplace
validators were not rerun because this repository does not yet document a
pinned invocation for them; they are not claimed for the current unreleased
change.

Ordinary reinstall/list smoke passed for the exact published `v0.1.1` tag on
`codex-cli 0.148.0-alpha.9` and Claude Code `2.1.214`; a projectless Codex
updater also moved one installed profile from `0.1.0` to `0.1.1` while
normalized before/after inventories showed every unrelated plugin and
marketplace unchanged. The published `0.1.0` candidate previously passed its
own packaging validators and install/list smoke on `codex-cli
0.147.0-alpha.6.5` and Claude Code `2.1.214`. Each observation applies only to
its exact release, build, and profile. They do not prove privacy isolation,
model behavior, semantic parity, cache custody, rollback, or general host
support.

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
