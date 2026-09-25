---
name: status
description: Read Kata routing health, unresolved choices and last-verified destination evidence without changing apps or starting runs.
---

# Kata status

Read [the operating contract](../../references/contract.md) and hydrate its live
guide. This operation is read-only. Check the live Review queue and available
cloud run state; use existing authenticated access without printing credentials.
If cloud access is unavailable, say so rather than infer health from old files.

Distinguish routing failures, a finished run awaiting a human choice, and open
work in Todoist/Linear. Report scope, last check time, actual exceptions and the
next useful action. A terminal needs_review run is not still running. Do not
start another session, apply answers or change Processing from a status request.
