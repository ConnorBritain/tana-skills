# Tana skills — Kata

Reusable Codex and Claude Code skills for reviewing Tana capture decisions and
reconciling their linked work. The repository is the package source; private
Tana context supplies each installation's schema, accounts and destinations.

| Skill | Purpose |
|---|---|
| `review` | Reconcile first, present genuine remaining choices, and apply authorized answers |
| `reconcile` | Repair stale Tana routing status from verified destination evidence |
| `status` | Read-only coverage, remaining choices and connection/automation status |
| `nightly` | Scoped Kata 02 batch contract; requires a configured coordinator, private instance file and valid run grant |

Claude commands are `/kata:review`, `/kata:reconcile`, and `/kata:status`.
In Codex, select the corresponding Kata skill. A guide link can be configured
once in the agent environment or supplied with the request; no Thought link is
needed when the guide identifies the review queue.

## Install

Claude Code:

```sh
claude plugin marketplace add ConnorBritain/tana-skills
claude plugin install kata@tana-skills
```

Codex:

```sh
codex plugin marketplace add ConnorBritain/tana-skills
codex plugin add kata@tana-skills
```

Start a fresh session after installation. Connect the apps required by your
private guide separately. This package does not create credentials, connect
accounts, install background hooks or activate a cloud routine.

## Scheduled use

Kata 01 is the capture-to-action workflow. Kata 02 is the action-to-Tana
reconciliation workflow: inspect existing destinations, apply saved decision
revisions, and close source routing only when every candidate is resolved.

A Claude cloud routine may use skills committed to its selected repository.
It still needs private configuration, scoped connector access and durable
coordination with other writers. A local plugin installation alone is not a
cloud installation. The `nightly` skill is the versioned cloud procedure. Its helpers, coordinator
and private instance configuration are being implemented separately; this repository does not claim a working hosted
service. See the [operating contract](plugins/kata/references/contract.md).

## Data boundaries

Keep recordings, transcripts, family/employer context, contact details, private
workspace/node IDs, tokens and run evidence outside this public repository.
Examples must be synthetic. `.local/` and environment files are ignored.

Processed means capture routing is handled. Tasks may still be open in their
owning apps. Park and decline are valid decisions without creating new tasks.
Original captures and historical receipts remain intact.
