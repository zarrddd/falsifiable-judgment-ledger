#!/usr/bin/env python3
"""Adjudicate a pending judgment on or after its expiry date.

Usage: python3 tools/resolve.py <ledger.json> \
           --id J-YYYY-NNN --status correct|partial|wrong --note TEXT \
           [--on YYYY-MM-DD (default: today)]

Discipline enforced at write time (spec §2):
  * judging before verify_by is refused — the expiry date may not be ignored,
    in either direction (no premature victory laps);
  * --on may not be in the future: a verdict is recorded when it is made,
    not postdated to when it would become legitimate;
  * an adjudicated entry is final: no re-judging, no status flips
    (factual slips go into corrections[], by hand, with the original kept);
  * a resolution ships with its note — partial especially must state
    exactly what "partial" means (spec discipline 6).
Single-writer tool (no file locking). Exit 0 = adjudicated; exit 1 = refused.
"""
import argparse, datetime, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from new_entry import refuse, flat, parse_date, load_ledger, write_validated

def main():
    p = argparse.ArgumentParser(epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("ledger")
    p.add_argument("--id", required=True)
    p.add_argument("--status", required=True, choices=["correct", "partial", "wrong"])
    p.add_argument("--note", required=True)
    p.add_argument("--on", default=datetime.date.today().isoformat())
    a = p.parse_args()

    note = flat(a.note)
    if not note: refuse("resolution_note is empty — say how you judged it")
    if len(note) > 500: refuse("resolution_note longer than 500 chars (schema maxLength)")
    on = parse_date(a.on, "--on")
    if on > datetime.date.today():
        refuse(f"--on {on.isoformat()} is in the future — verdicts are recorded when made, not postdated")

    if not os.path.isfile(a.ledger):
        refuse(f"ledger not found: {a.ledger} (create one with tools/new_entry.py)")
    doc = load_ledger(a.ledger)
    entry = next((e for e in doc["entries"]
                  if isinstance(e, dict) and e.get("id") == a.id), None)
    if entry is None: refuse(f"no entry with id {a.id}")
    if entry.get("status") != "pending":
        refuse(f"{a.id} already adjudicated as '{entry.get('status')}' — "
               "verdicts are final; use corrections[] for factual slips")
    try:
        expiry = datetime.date.fromisoformat(entry["verify_by"])
    except (KeyError, TypeError, ValueError):
        refuse(f"{a.id} has no valid verify_by — run tools/validate.py and fix the ledger first")
    if on < expiry:
        refuse(f"{a.id} expires {entry['verify_by']} — judge on or after expiry "
               "(spec discipline 1: no early verdicts)")

    entry["status"] = a.status
    entry["resolved_on"] = on.isoformat()
    entry["resolution_note"] = note

    write_validated(a.ledger, doc)
    print(f"OK: {a.id} -> {a.status} (resolved_on {on.isoformat()})")

if __name__ == "__main__":
    main()
