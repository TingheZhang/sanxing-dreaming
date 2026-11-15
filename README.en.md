# 三省 · Sanxing

Sanxing is a research-dreaming Skill for research agents. It revisits original evidence and adds literature-driven ideation only when the caller supplies papers or an explicitly scoped paper corpus. It runs the smallest check only when its result could change a stated judgment.

[中文版 README](README.md)

## The name

The name comes from Zengzi’s words in the first book of the *Analects*, 「吾日三省吾身」, about examining oneself each day. 三省 is read *sān xǐng*, with 省 meaning to reflect or examine. Sanxing uses the name to frame three questions for each research pass.

1. **Which old judgment should change?**

   Start from newly available original records. Check prior memories, summaries, and status claims. Keep the source, revision, and page or section anchor for important claims.

2. **When papers are supplied, what new hypothesis emerges?**

   Read papers only when the caller supplies papers, paper links, or a clearly scoped literature directory. Look for connections, tensions, and boundary conditions in those inputs. Turn a connection into a hypothesis with competing predictions and explicit inputs. Skip literature ideation when no literature is supplied.

3. **What result would change my mind?**

   Run a minimal check only when credible frozen inputs are available and different outcomes would change a named judgment or action. Otherwise deliver an executable protocol with inputs, split, metric, threshold, and falsifier.

## Scope

Sanxing is for projects that need to revisit earlier summaries and decide what to test next. A pass can run a small reproducible check when frozen data already exists.

Each caller provides a project identifier, scope, approved read-only project records, independent output directory, and execution budget. Sanxing is model-, memory-product-, and language-agnostic. It does not train production models, rewrite formal project memory, access sealed test sets, or relabel an old summary as a new experiment.

## Prompt template

Put the repository somewhere your agent can read and give it the path to `SKILL.md`. Fill in the fields below and send the prompt to the agent. An example budget is 30 minutes for a single local CPU check. Use `none` for the previous checkpoint on your first pass.

```text
First read <path_to_repo>/SKILL.md and follow research-dreaming 0.3.1.
The project is <project> and the scope is <scope>.
Approved read-only project evidence is <approved_project_records>.
Write results to the independent directory <output_dir>.
The execution budget is <budget>.
The previous successful checkpoint is <previous_checkpoint_or_none>.

First build a complete catalog.json for the scope and run the incremental evidence scan.
Choose one question from the original project evidence that could change a project judgment.
Record evidence anchors, competing predictions, inputs, split or replication unit, metric, uncertainty, falsifier, and threshold.
Run the smallest check only when credible frozen inputs exist and the result would change the named judgment.
Otherwise write PLAN_ONLY and name the missing inputs and next access required.
Write all reports, commands, hashes, and handoff material to the independent directory.
Do not train production models, access sealed test data, or update formal memory.
```

To enable literature ideation, append “Use <paper files, paper links, or a scoped paper directory> to develop hypotheses for this pass, and cite pages or sections.” Searching for additional papers requires separate authorization.

The caller may ask the agent to choose the topic. Do not carry a previous agent's hypothesis into a new pass as its question.

## Pass lifecycle

1. Build `catalog.json` with stable IDs and a complete inventory for the agreed scope.
2. Run the incremental scan and inspect added, changed, removed, and unchanged sources.
3. Read original evidence from added and changed sources. Inspect paper pages or sections only when literature inputs were supplied.
4. Choose one falsifiable question that could affect a named judgment. Separate observed, inferred, proposed, and unresolved claims.
5. Define competing predictions, inputs, split or replication unit, metric, uncertainty, falsifier, and threshold.
6. Decide whether to run the minimal check. If frozen evidence is missing, deliver the protocol with `PLAN_ONLY`.
7. Save the report, machine-readable result, exact commands, hashes, logs, and handoff.
8. Advance a checkpoint only after the scan and evidence review are verified.

## Incremental scan and checkpoint

Let the agent handle this step or run the bundled Python script yourself. This example assumes `catalog.json` is in the repository root. Replace `sources` with the complete inventory for the agreed scope. Relative source paths resolve from the catalog's directory. Command-line paths resolve from your working directory.

```json
{
  "project": "example-project",
  "scope": "notes-and-priority-evidence",
  "complete_inventory": true,
  "sources": [
    {"id": "project-index", "path": "inputs/MEMORY.md"}
  ]
}
```

For a supplied directory, enumerate the in-scope papers individually in `sources`. Each `path` points to a file.

Run the first scan from the repository root. The code blocks use Bash. In Windows PowerShell 5.1, use `| Set-Content -Encoding utf8 <output-path>` to write the JSON.

```bash
mkdir -p runs/first
python scripts/evidence_delta.py scan --catalog catalog.json > runs/first/DELTA.json
```

The first scan marks all catalog entries as added. After review, write `RESULT.json` with `project`, `scope`, `status`, and `delta_sha256`, the SHA-256 hash of the actual saved `DELTA.json` file. Use the first command below to compute the hash. In `reviewed.json`, list the stable IDs you reviewed and documented, for example `["project-index"]`. Run the second command after verifying the review.

```bash
python -c "import hashlib; from pathlib import Path; print(hashlib.sha256(Path('runs/first/DELTA.json').read_bytes()).hexdigest())"
python scripts/evidence_delta.py checkpoint --scan runs/first/DELTA.json --result runs/first/RESULT.json --reviewed runs/first/reviewed.json > runs/first/CHECKPOINT.json
```

Start the next pass in a fresh output directory and reuse the last successful checkpoint for the same project and scope. Start a new baseline when the scope changes.

```bash
mkdir -p runs/second
python scripts/evidence_delta.py scan --catalog catalog.json --previous runs/first/CHECKPOINT.json > runs/second/DELTA.json
```

A completed protocol without an executed check uses `status: COMPLETED` and `verification_status: PLAN_ONLY`. Record the frozen inputs and result for an executed check. Use `UNRESOLVED` or `NOT_VERIFIED` when the evidence or inventory cannot be verified, and keep the previous checkpoint.

## Output directory

A successful pass usually contains the following files.

- `DREAM_REPORT.md` for the question, evidence map, competing predictions, decision rule, and page or section anchors for any papers used
- `RESULT.json` for machine-readable status, scope, hashes, and next steps
- `RUN.md` for executed and planned commands
- `DELTA.json` for the incremental scan
- `CHECKPOINT.json` for the reviewed-source checkpoint
- `reviewed.json` for stable IDs with completed evidence dispositions

Keep the run in an independent directory. Update formal project memory only after human review.

## Example

Suppose the question is whether a model component yields at least a 0.5% relative error reduction in two cell contexts. Even without papers, the agent can define the question from project evidence and compare two capacity-matched models on the same targets and frozen held-out split. When the caller supplies papers, the agent can use their evaluation methods as traceable hypothesis inputs. If per-target predictions and response data are missing, the agent must not call a historical summary a new result. It should write `PLAN_ONLY` and list the required predictions, labels, split, and weight files.

## Included files

- [SKILL.md](SKILL.md) research workflow, version 0.3.1
- [scripts/evidence_delta.py](scripts/evidence_delta.py) incremental evidence scan and checkpoint utility
- [README.md](README.md) Chinese documentation

