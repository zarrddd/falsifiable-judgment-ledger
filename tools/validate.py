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
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# String length bounds mirrored from schema/*.json — this validator is the
# conformance arbiter (SPEC §5), so it must enforce everything the schema declares.
LEN = {"claim": (8, None), "falsifier": (8, None), "track": (None, 40),
       "resolution_note": (None, 500)}

def d(s):
    if not DATE_RE.match(s):  # fromisoformat on 3.11+ accepts more forms; the spec says YYYY-MM-DD only
        raise ValueError(s)
    return datetime.date.fromisoformat(s)

def check_str(e, field, errs, tag, min_max):
    if field not in e: return
    v, (lo, hi) = e[field], min_max
    if not isinstance(v, str):
        errs.append(f"{tag}: {field} must be a string"); return
    if lo and len(v) < lo: errs.append(f"{tag}: {field} shorter than {lo} chars (schema minLength)")
    if hi and len(v) > hi: errs.append(f"{tag}: {field} longer than {hi} chars (schema maxLength)")

def fail(msgs):
    for m in msgs: print("FAIL:", m)
    sys.exit(1)

def load(path):
    """Read a ledger with clean one-line failures (utf-8-sig tolerates a BOM)."""
    try:
        doc = json.load(open(path, encoding="utf-8-sig"))
    except FileNotFoundError:
        print(f"FAIL: ledger not found: {path} (create one with tools/new_entry.py)"); sys.exit(1)
    except json.JSONDecodeError as ex:
        print(f"FAIL: ledger is not valid JSON: {path} ({ex})"); sys.exit(1)
    if not isinstance(doc, dict):
        print("FAIL: ledger must be a JSON object"); sys.exit(1)
    return doc

def main(path):
    errs = []
    doc = load(path)
    extra = set(doc) - {"ledger_version","steward","fictional","notes","entries"}
    if extra: errs.append(f"ledger has unknown fields: {sorted(extra)}")
    check_str(doc, "steward", errs, "ledger", (None, 80))
    for n in doc.get("notes", []):
        if set(n) - {"on","note"}: errs.append("ledger note has unknown fields")
        check_str(n, "note", errs, "ledger note", (None, 500))
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
        if not isinstance(e["id"], str) or not ID_RE.match(e["id"]):
            errs.append(f"{tag}: id must match J-YYYY-NNN"); continue
        if e["id"] in seen: errs.append(f"{tag}: duplicate id")
        seen.add(e["id"])
        for f, mm in LEN.items(): check_str(e, f, errs, tag, mm)
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
            check_str(c, "note", errs, f"{tag} correction", (None, 300))
    if errs: fail(errs)
    print(f"OK: {len(doc['entries'])} entries valid")

if __name__ == "__main__":
    if len(sys.argv) != 2: print(__doc__); sys.exit(2)
    main(sys.argv[1])
