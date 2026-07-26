#!/usr/bin/env python3
"""List entries whose verify_by has passed but status is still pending.

Usage: python3 tools/expiry_check.py <ledger.json> [--as-of YYYY-MM-DD]
Exit 0 = none overdue; exit 1 = overdue entries exist (listed).
The whole point of an expiry date is that it may not be ignored.
"""
import json, os, sys, datetime

def main(argv):
    path = argv[1]
    as_of = datetime.date.today()
    if len(argv) == 4 and argv[2] == "--as-of":
        as_of = datetime.date.fromisoformat(argv[3])
    if not os.path.isfile(path):
        print(f"FAIL: ledger not found: {path} (create one with tools/new_entry.py)"); return 1
    try:
        doc = json.load(open(path, encoding="utf-8-sig"))
    except json.JSONDecodeError as ex:
        print(f"FAIL: ledger is not valid JSON ({ex})"); return 1
    overdue = [e for e in doc.get("entries", [])
               if e.get("status") == "pending"
               and datetime.date.fromisoformat(e["verify_by"]) < as_of]
    if not overdue:
        print("OK: no overdue judgments"); return 0
    for e in overdue:
        print(f"OVERDUE: {e['id']} verify_by={e['verify_by']} — judge it, on the record")
    return 1

if __name__ == "__main__":
    if len(sys.argv) not in (2, 4): print(__doc__); sys.exit(2)
    sys.exit(main(sys.argv))
