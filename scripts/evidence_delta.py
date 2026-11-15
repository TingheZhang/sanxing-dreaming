#!/usr/bin/env python3
"""Deterministic, portable evidence inventory and review checkpoint helper."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCHEMA = "research-dreaming.evidence-delta/0.2"


class ValidationError(Exception):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def load_json(path: str) -> object:
    try:
        with open(path, "r", encoding="utf-8-sig") as handle:
            return json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"cannot read JSON {path!r}: {exc}")


def load_json_bytes(raw: bytes, label: str) -> object:
    try:
        return json.loads(raw.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        fail(f"cannot parse {label}: {exc}")


def obj(value: object, label: str) -> dict:
    if not isinstance(value, dict):
        fail(f"{label} must be an object")
    return value


def text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{label} must be a non-empty string")
    return value


def fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    except (OSError, UnicodeError) as exc:
        fail(f"declared local source is unreadable: {path}: {exc}")
    return digest.hexdigest()


def inventory(catalog_path: str) -> tuple[str, str, dict[str, dict]]:
    raw = obj(load_json(catalog_path), "catalog")
    project, scope = text(raw.get("project"), "catalog.project"), text(raw.get("scope"), "catalog.scope")
    if raw.get("complete_inventory") is not True:
        fail("catalog.complete_inventory must be true")
    sources = raw.get("sources")
    if not isinstance(sources, list):
        fail("catalog.sources must be an array")
    try:
        root = Path(catalog_path).resolve().parent
    except OSError as exc:
        fail(f"cannot resolve catalog path: {exc}")
    records: dict[str, dict] = {}
    for index, source in enumerate(sources):
        source = obj(source, f"catalog.sources[{index}]")
        sid = text(source.get("id"), f"catalog.sources[{index}].id")
        if sid in records:
            fail(f"duplicate source id: {sid}")
        has_path, has_revision = "path" in source, "revision" in source
        if has_path == has_revision:
            fail(f"source {sid!r} must contain exactly one of path or revision")
        if has_path:
            raw_path = text(source.get("path"), f"source {sid}.path")
            try:
                path = Path(raw_path)
                if not path.is_absolute():
                    path = root / path
                path = path.resolve()
            except (OSError, RuntimeError, ValueError) as exc:
                fail(f"cannot resolve source {sid!r} path: {exc}")
            if not path.is_file():
                fail(f"declared local source is missing or not a file: {path}")
            records[sid] = {"id": sid, "kind": "file", "locator": str(path), "fingerprint": fingerprint(path)}
        else:
            revision = text(source.get("revision"), f"source {sid}.revision")
            records[sid] = {"id": sid, "kind": "revision", "locator": revision, "fingerprint": revision}
    return project, scope, records


def record_map(value: object, label: str) -> dict[str, dict]:
    data = obj(value, label)
    out = {}
    for sid, record in data.items():
        if not isinstance(sid, str):
            fail(f"{label} contains a non-string id")
        rec = obj(record, f"{label}[{sid!r}]")
        if rec.get("id") != sid or rec.get("kind") not in ("file", "revision"):
            fail(f"invalid record {label}[{sid!r}]")
        for key in ("locator", "fingerprint"):
            text(rec.get(key), f"{label}[{sid!r}].{key}")
        out[sid] = {"id": sid, "kind": rec["kind"], "locator": rec["locator"], "fingerprint": rec["fingerprint"]}
    return out


def checkpoint_state(raw: object, label: str) -> tuple[str, str, dict[str, dict]]:
    data = obj(raw, label)
    if data.get("schema_version") != SCHEMA or data.get("command") != "checkpoint":
        fail(f"{label} is not a valid checkpoint")
    project, scope = text(data.get("project"), f"{label}.project"), text(data.get("scope"), f"{label}.scope")
    if "accepted" not in data:
        fail(f"{label}.accepted is required")
    return project, scope, record_map(data["accepted"], f"{label}.accepted")


def identity(record: dict) -> tuple[str, str]:
    return record["kind"], record["fingerprint"]


def make_diff(accepted: dict[str, dict], current: dict[str, dict]) -> dict:
    added, changed, removed, unchanged = {}, {}, {}, {}
    for sid, record in current.items():
        old = accepted.get(sid)
        if old is None:
            added[sid] = record
        elif identity(old) == identity(record):
            unchanged[sid] = record
        else:
            changed[sid] = {"previous": old, "current": record}
    for sid, old in accepted.items():
        if sid not in current:
            removed[sid] = {"previous": old}
    return {"added": added, "changed": changed, "removed": removed, "unchanged": unchanged}


def scan(args: argparse.Namespace) -> dict:
    project, scope, current = inventory(args.catalog)
    accepted: dict[str, dict] = {}
    previous = None
    if args.previous:
        previous = obj(load_json(args.previous), "previous checkpoint")
        p_project, p_scope, accepted = checkpoint_state(previous, "previous checkpoint")
        if (p_project, p_scope) != (project, scope):
            fail("previous checkpoint project/scope does not match catalog")
    diff = make_diff(accepted, current)
    added, changed, removed = diff["added"], diff["changed"], diff["removed"]
    return {"schema_version": SCHEMA, "command": "scan", "project": project, "scope": scope,
            "complete_inventory": True, "previous": previous,
            "candidate": {"project": project, "scope": scope, "sources": current}, "diff": diff,
            "status": "CHANGES_FOUND" if (added or changed or removed) else "NO_NEW_EVIDENCE"}


def checkpoint(args: argparse.Namespace) -> dict:
    try:
        scan_bytes = Path(args.scan).read_bytes()
    except OSError as exc:
        fail(f"cannot read scan bytes: {exc}")
    scan_data = obj(load_json_bytes(scan_bytes, "scan bytes"), "scan")
    if scan_data.get("schema_version") != SCHEMA or scan_data.get("command") != "scan":
        fail("scan is not a valid evidence-delta scan")
    if scan_data.get("complete_inventory") is not True:
        fail("scan.complete_inventory must be true")
    project, scope = text(scan_data.get("project"), "scan.project"), text(scan_data.get("scope"), "scan.scope")
    candidate = obj(scan_data.get("candidate"), "scan.candidate")
    if (candidate.get("project"), candidate.get("scope")) != (project, scope):
        fail("scan candidate project/scope mismatch")
    current = record_map(candidate.get("sources"), "scan.candidate.sources")
    diff = obj(scan_data.get("diff"), "scan.diff")
    changes: dict[str, str] = {}
    for kind in ("added", "changed", "removed"):
        section = obj(diff.get(kind, {}), f"scan.diff.{kind}")
        for sid in section:
            if sid in changes:
                fail(f"scan repeats changed id: {sid}")
            changes[sid] = kind
    result = obj(load_json(args.result), "result")
    if result.get("project") != project or result.get("scope") != scope:
        fail("result project/scope does not match scan")
    if result.get("delta_sha256") != hashlib.sha256(scan_bytes).hexdigest():
        fail("result.delta_sha256 does not match exact scan JSON bytes")
    status = result.get("status")
    if status not in ("COMPLETED", "NO_NEW_EVIDENCE"):
        fail("result.status must be COMPLETED or NO_NEW_EVIDENCE")
    if status == "NO_NEW_EVIDENCE" and changes:
        fail("NO_NEW_EVIDENCE is only valid when the scan has no changes")
    reviewed_raw = load_json(args.reviewed)
    if not isinstance(reviewed_raw, list) or any(not isinstance(x, str) or not x.strip() for x in reviewed_raw):
        fail("reviewed file must contain a JSON array of non-empty IDs")
    if len(set(reviewed_raw)) != len(reviewed_raw):
        fail("reviewed IDs must be unique")
    unknown = [sid for sid in reviewed_raw if sid not in changes]
    if unknown:
        fail(f"reviewed IDs are not in scan changes: {unknown}")
    if not changes and reviewed_raw:
        fail("cannot review IDs when scan has no changes")
    accepted: dict[str, dict] = {}
    prior = scan_data.get("previous")
    if prior is not None:
        p_project, p_scope, accepted = checkpoint_state(prior, "scan.previous")
        if (p_project, p_scope) != (project, scope):
            fail("scan.previous project/scope does not match scan")
    if diff != make_diff(accepted, current):
        fail("scan.diff does not match its accepted baseline and candidate")
    for sid in reviewed_raw:
        if changes[sid] == "removed":
            accepted.pop(sid, None)
            continue
        record = current[sid]
        if record["kind"] == "file" and fingerprint(Path(record["locator"])) != record["fingerprint"]:
            fail(f"reviewed local source changed after scan: {sid}")
        accepted[sid] = record
    return {"schema_version": SCHEMA, "command": "checkpoint", "project": project, "scope": scope,
            "accepted": {sid: accepted[sid] for sid in sorted(accepted)}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    scan_parser = sub.add_parser("scan")
    scan_parser.add_argument("--catalog", required=True)
    scan_parser.add_argument("--previous")
    scan_parser.set_defaults(handler=scan)
    cp_parser = sub.add_parser("checkpoint")
    cp_parser.add_argument("--scan", required=True)
    cp_parser.add_argument("--result", required=True)
    cp_parser.add_argument("--reviewed", required=True)
    cp_parser.set_defaults(handler=checkpoint)
    args = parser.parse_args()
    try:
        output = args.handler(args)
    except ValidationError as exc:
        print(f"evidence_delta: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(output, ensure_ascii=True, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
