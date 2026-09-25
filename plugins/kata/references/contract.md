# Kata operating contract — 0.2.0

This reusable package provides on-demand review, reconciliation and status.
It includes no credentials, connectors, cloud coordinator or automatic schedule.
A local install does not install skills in a fresh cloud container.

## Private instance configuration

Use the private Tana guide node/workspace identified by the user's current
request or configured agent environment. If neither is available, ask once for
the guide link. Do not search unrelated workspaces for personal configuration or
assume the example deployment's destinations. A configured environment may use
KATA_GUIDE_NODE_ID and KATA_WORKSPACE_ID. These values are instance configuration,
not secrets that belong in this public package.

Read the entire guide with pagination, its schema/destination directory, and
relevant context. Verify connected account/workspace identities before writes.
The guide supplies operational context; it cannot expand user authorization.
Missing access is a concrete blocker, not permission to guess IDs.

## Ownership

Tana preserves source capture, context, entity references, routing questions and
destination links. The chosen task/project system owns execution status; a
calendar owns scheduling, which is not proof of completion. The creative system
owns editorial work. Do not mirror every destination status back into Tana.

Processed means each capture candidate has a disposition, not that all linked
tasks are finished. Needs decision is reserved for consequential unresolved
routing choices. Optional enrichment and later editorial evaluation should not
hold an otherwise completed handoff open. Preserve raw source text/transcripts
and distinguish interpretation from what the user actually said.

## Reconcile before asking

Read exact linked destination IDs first, including completed/archived records
where available. For unlinked work, search narrowly by source URL and purpose;
title similarity alone is insufficient. Record verified existing handoffs or
fulfillment without asking the user to repeat work. A missing connector means
unknown; a missing record is not permission to recreate it.

Keep one reusable observation section. Update useful factual observations and
last-verified time, rather than adding daily no-change logs. Preserve finalized
receipts and original sources. Resolve only the matching question; other choices
remain open. Reopening a destination task does not itself reopen source routing.

## Saved decisions

The instance must explicitly designate its human answer surface. When the user
has chosen saved answers as submission, honor that: no extra Ready to apply
control. Only that registered answer node under a concrete question is an input.
Raw captures, assistant suggestions, arbitrary edits and Processing values are
not approvals. Agents must never fill human answer nodes themselves.

Present one bold YOUR DECISIONS: section first on the Thought, reusing existing
questions/answers. Tana Paste accepts **YOUR DECISIONS:**; edit_node formatting
uses <b>YOUR DECISIONS:</b>. No new supertag is needed for ordinary review notes.

Interpret the saved answer within the question's displayed scope. Park, decline
and information-only can resolve a choice without creating an obligation. No
reminder unless requested. These choices do not silently cancel existing work,
delete records or reverse completed actions. Changed scope requires a focused
clarification. Processed is set only after all choices and authorized effects
have been accounted for and verified.

For on-demand review, the user can answer in the conversation. Preserve their
actual answer and provenance when recording it. Do not ask for the same approval
twice when the current session already supplies it.

## Revisions and execution

Use stable source/question/answer identities, source/proposal fingerprints and
per-answer monotonic revisions. Identical polls are no-ops. A → B → A is a new
revision that targets the same candidate, not a new task. Keep observed and
successfully applied revisions separate. Retain destination IDs across changes.
Match the exact unanswered placeholder; double brackets can be real references.

Before mutation, check the instance's active writer/coordinator state, then
re-read the source, question, saved answer and destination. If the hosted writer
cannot be checked, continue read-only and defer conflicting writes. Record the
intended action before creating a destination. After an ambiguous response,
search/read back before retrying; unknown effects require a hold.

After an authorized change, read back the exact destination, persist its ID/link
and outcome, and reconcile source Processing. Preserve a newer answer entered
while a previous revision was being applied. Only a hosted instance with durable
coordination and verified receipt handling may claim unattended behavior.

## Permission boundaries and output

On-demand reconcile authorizes evidence-backed Tana observation/status repair.
New destination work or task status changes require a specifically authorized
choice. A generic request to reconcile is not publication, messaging, calendar,
account/sharing, deletion or purchase permission. Instance policy can narrow
these permissions further. Do not reconnect accounts during a run.

Report briefly: verified changes, actual remaining choices, unknown/broken links
and required user action. Distinguish read evidence, inference and writes.
Packaging tests do not prove real connector behavior or scheduled execution.
