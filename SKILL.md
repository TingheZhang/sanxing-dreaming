---
name: research-dreaming
description: Run an evidence-bounded research pass with incremental project-evidence review, optional caller-supplied literature, testable hypotheses, and reproducible handoff artifacts.
metadata:
  version: 0.3.1
  scope: cross-agent research workflow
  incremental-evidence: true
  literature-synthesis: true
---

# Research dreaming

Use this skill for a bounded research pass across project records, with optional literature synthesis. Preserve the incremental review mechanics from `agent-dream`: orient, gather, compare, and hand off. The workflow is model-neutral and does not require a runtime experiment when evidence cannot change a decision.

## Inputs and boundaries

Read the project identifier and handoff summary supplied by the caller. Read formal memory and original evidence through the approved project reader or repository paths. Treat summaries, old status claims, generated indexes, and prior hypotheses as claims to check. Keep raw sessions and credentials local.

The caller must provide an independent output directory and an execution budget. Create no production writes, deployments, service changes, model-training jobs, or formal-memory updates unless explicitly authorized. Do not assume a previous agent's proposed experiment is the question for this run.

Use the latest successful checkpoint named in the project handoff when its `project` and exact `scope` match. Build `catalog.json` from the authorized source list or a complete enumeration within the agreed scope. Choose stable IDs that survive renames. Use verified immutable revisions for remote items and resolve their IDs through the project reader. Give a changed scope a fresh baseline. The first scan without a predecessor marks current items as added.

```json
{
  "project": "example-project",
  "scope": "notes-and-priority-evidence",
  "complete_inventory": true,
  "sources": [
    {"id": "project-index", "path": "inputs/MEMORY.md"},
    {"id": "approved-reader:receipt-17", "revision": "immutable-revision-3"}
  ]
}
```

Resolve local paths relative to `catalog.json` or supply absolute paths. Set `complete_inventory` to `true` after listing all in-scope sources, including unchanged items.

## Optional literature mode

Activate literature synthesis only when the caller explicitly supplies papers, paper links, or a scoped literature corpus for this run. Otherwise, use project evidence and skip corpus discovery, paper search, and literature synthesis. An omitted corpus is a valid default.

Include in-scope literature in the catalog. Enumerate files in a supplied directory individually and record unreadable sources as unresolved. Read supplied material for ideas, disagreements, and boundary conditions. A single paper can inform a hypothesis alongside project evidence. Cite pages or sections for every literature claim and record what each used paper contributes. Searching for additional papers requires separate explicit authorization. For authorized searches, use generic methodological queries, record them, and keep private project details local.

## Incremental evidence prepass

Before choosing a question, run:

```text
python scripts/evidence_delta.py scan --catalog <catalog.json> [--previous <checkpoint.json>]
```

Save successful JSON stdout as `DELTA.json`. Inspect added, changed, removed, and unchanged IDs. A changed locator with the same fingerprint is unchanged. Read added and changed sources first. Follow old pointers when they help interpret an item, verify a contradiction, or address a requested topic. Preserve the old claim alongside newer evidence. Distinguish a catalog removal from a missing or unreadable declared file.

If the verified delta has no changes and there is no requested topic or manual override, record `NO_NEW_EVIDENCE` with a short report. If enumeration is incomplete, the scan errors, or the promised predecessor is unavailable or mismatched, preserve the error in the run record and mark incremental review `NOT_VERIFIED`. A bounded manual check may continue with available evidence. Checkpoint advancement requires a verified scan.

## Decision rule and workflow

1. Build an evidence map from relevant delta sources with identity, status, date, revision, exact claim, and section/page provenance. Separate observed, inferred, proposed, and unresolved claims.
2. If literature mode is active, use connections in the supplied material to generate or refine a hypothesis.
3. Choose one impactful, falsifiable question. Name the interpretation or action it could change and why it matters.
4. Write a hypothesis and competing explanation, then define inputs, split/test unit, metric, uncertainty, falsifier, decision threshold, and the exact evidence needed.
5. Decide whether to run a check: run only the smallest authorized, bounded check when (a) real, frozen, relevant evidence is accessible and (b) plausible differing outcomes would change the named interpretation or action. Do not force a runtime for a plan-only case.
6. If those conditions are not met, deliver an executable falsifiable protocol instead: competing predictions, inputs, split/test unit, metric, falsifier/decision threshold, why execution is deferred, and the exact next access required.
7. A surrogate is allowed only when it can inform a named methodological decision. Label surrogate and exploratory results clearly; never call them project results or hypothesis confirmation.
8. Save machine-readable results, exact command, hashes, logs, report, and handoff in the independent directory. Reuse frozen inputs and do not use held-out labels/results for feature, threshold, or group choice.

## Result and checkpoint rules

`RESULT.json` records exact `project` and `scope` plus `delta_sha256`, the SHA-256 of the saved `DELTA.json` bytes when available. A verified pass can have status `COMPLETED`, including a credible null result or a protocol that meets the plan requirements. For the protocol, set `verification_status` to `PLAN_ONLY` and record why execution was deferred. `NO_NEW_EVIDENCE` requires an empty delta. Failed, unresolved, or unverifiable work remains `UNRESOLVED` or `NOT_VERIFIED` and cannot advance the checkpoint.

After verifying the artifacts, write the list of reviewed stable IDs to a JSON array and run:

```text
python scripts/evidence_delta.py checkpoint --scan <DELTA.json> --result <RESULT.json> --reviewed <reviewed.json>
```

Save successful stdout as `CHECKPOINT.json` when eligible. Include an ID only after recording a disposition for its addition, revision, or removal and confirming the evidence still matches the scan. A plan can record completed evidence review separately from open scientific questions. Deferred items keep their previous revisions and recur next time. Keep each checkpoint with its run artifacts.

## Output contract

Write `DREAM_REPORT.md`, `RESULT.json`, and `RUN.md`, plus `DELTA.json` for a successful scan and `CHECKPOINT.json` when eligible. Include the named decision, sources with section or page anchors, competing predictions, executed check or deferred protocol, and acceptance criteria. Label commands as executed or planned. Use stable relative links for run artifacts, UTC timestamps, and a run ID.

## Memory handoff

AI Memory carries the structured cross-agent handoff. Record the event ID, session identifier, Skill version, exact project/scope, progress, status, independent output path, delta and optional checkpoint, next step, and acceptance condition. A retry keeps the same event ID and identical payload. Formal project knowledge belongs in Basic Memory after review, with the evidence scope, source run, and open questions.

## Stop conditions

Return `UNRESOLVED` or `NOT_VERIFIED` when provenance, required inputs, catalog completeness, or the authorized path is not established. Do not invent plausible values, silently broaden scope, force a runtime, or advance a checkpoint without verified evidence.
