#!/usr/bin/env python3
"""Validate a ledger file against the spec schemas (no external deps).

Usage: python3 tools/validate.py <ledger.json>
Exit 0 = valid; exit 1 = invalid (reasons printed).
Checks: closed fields, id pattern, enum closure, date sanity,
        status/resolution consistency, duplicate ids.
(Expiry discipline is checked separately by tools/expiry_check.py.)
"""
import json, re, sys, datetime

ENTRY_FIELDS = {"id","claim","falsifier","track","stated_on","verify_by",
                "status","resolved_on","resolution_note","corrections"}
REQUIRED = {"id","claim","falsifier","stated_on","verify_by","status"}
STATUS = {"pending","correct","partial","wrong"}
ID_RE = re.compile(r"^J-\d{4}-\d{3}$")

def d(s):
    return datetime.date.fromisoformat(s)

def fail(msgs):
    for m in msgs: print("FAIL:", m)
    sys.exit(1)

def main(path):
    errs = []
    doc = json.load(open(path, encoding="utf-8"))
    extra = set(doc) - {"ledger_version","steward","fictional","notes","entries"}
    if extra: errs.append(f"ledger has unknown fields: {sorted(extra)}")
    for n in doc.get("notes", []):
        if set(n) - {"on","note"}: errs.append("ledger note has unknown fields")
    if "ledger_version" not in doc or "entries" not in doc:
        errs.append("ledger_version and entries are required")
        fail(errs)
    seen = set()
    for i, e in enumerate(doc["entries"]):
        tag = e.get("id", f"entries[{i}]")
        ex = set(e) - ENTRY_FIELDS
        if ex: errs.append(f"{tag}: unknown fields {sorted(ex)} (additionalProperties is closed)")
        miss = REQUIRED - set(e)
        if miss: errs.append(f"{tag}: missing required {sorted(miss)}"); continue
        if not ID_RE.match(e["id"]): errs.append(f"{tag}: id must match J-YYYY-NNN")
        if e["id"] in seen: errs.append(f"{tag}: duplicate id")
        seen.add(e["id"])
        if e["status"] not in STATUS: errs.append(f"{tag}: status not in {sorted(STATUS)}")
        try:
            if d(e["verify_by"]) < d(e["stated_on"]):
                errs.append(f"{tag}: verify_by earlier than stated_on")
        except ValueError:
            errs.append(f"{tag}: dates must be ISO YYYY-MM-DD")
        if e["status"] != "pending" and "resolved_on" not in e:
            errs.append(f"{tag}: resolved status requires resolved_on")
        if e["status"] != "pending" and "resolved_on" in e:
            try:
                if d(e["resolved_on"]) < d(e["verify_by"]):
                    errs.append(f"{tag}: resolved_on earlier than verify_by (discipline: judge on or after expiry)")
            except ValueError:
                errs.append(f"{tag}: resolved_on must be ISO YYYY-MM-DD")
        if e["status"] == "pending" and "resolved_on" in e:
            errs.append(f"{tag}: pending entry must not carry resolved_on")
        for c in e.get("corrections", []):
            if set(c) - {"on","note"}: errs.append(f"{tag}: correction has unknown fields")
    if errs: fail(errs)
    print(f"OK: {len(doc['entries'])} entries valid")

if __name__ == "__main__":
    if len(sys.argv) != 2: print(__doc__); sys.exit(2)
    main(sys.argv[1])
