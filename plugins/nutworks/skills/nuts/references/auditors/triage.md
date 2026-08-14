# Triage Auditor

Act in a fresh context after Main Context, Concerns, and Verification are all
complete. Do not edit the target.

1. Inventory every finding from all three sources.
2. Merge only reports that share the same failure mode and evidence; preserve
   every source reference.
3. Map repeated decision boundaries to an existing stable FLAG ID.
4. Disposition every canonical concern as exactly one of:
   - `FIX` — resolve and verify before proceeding;
   - `FLAG` — a genuine user-owned product, architecture, public claim or
     interface, privacy/retention, destructive, money/account, policy, or
     publication choice; or
   - `ACCEPT` — a bounded residual risk within settled scope, with reasoning.
5. Report source counts, canonical counts, and omitted count. Omitted must be
   zero.

Bias toward `FIX` when a small in-scope correction resolves a concrete defect.
Do not turn agent-resolvable diagnostics or optional preferences into user
questions. A disposition does not grant mutation authority; the main runner
owns changes, verification, and phase routing.
