#!/usr/bin/env python3
"""Append a new judgment to a ledger (creates the ledger file if missing).

Usage: python3 tools/new_entry.py <ledger.json> \
           --claim TEXT --falsifier TEXT --verify-by YYYY-MM-DD \
           [--track TEXT] [--stated-on YYYY-MM-DD (default: today)]

Discipline enforced at write time (spec §1–2):
  * claim and falsifier must be substantial (schema minLength 8) — a judgment
    ships with its falsifier;
  * pasted text is flattened: runs of whitespace (including CR/LF) collapse to
    single spaces, so a claim is stored as the one sentence the spec demands;
  * dates are strict YYYY-MM-DD; verify_by must not precede stated_on;
  * id is auto-assigned J-YYYY-NNN (year of stated_on, max existing NNN + 1 —
    numbers are never reused, even across gaps);
  * status starts as pending; the result is validated by tools/validate.py
    before the ledger is replaced (fail-closed: an invalid result never
    touches the ledger).
Single-writer tool: there is no file locking — do not run concurrent writes
against one ledger. Exit 0 = entry written (id printed); exit 1 = refused.
"""
import argparse, datetime, json, os, re, subprocess, sys, tempfile

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def refuse(msg):
    print("REFUSED:", msg); sys.exit(1)

def flat(s):
    """Collapse all whitespace runs (CR, LF, tabs, ideographic space) to single spaces."""
    return re.sub(r"\s+", " ", s).strip()

def parse_date(s, what):
    if not DATE_RE.match(s): refuse(f"{what} must be ISO YYYY-MM-DD")
    try:
        return datetime.date.fromisoformat(s)
    except ValueError:
        refuse(f"{what} is not a real date: {s}")

def load_ledger(path):
    if not os.path.isfile(path):
        return {"ledger_version": "0.1", "entries": []}
    try:
        doc = json.load(open(path, encoding="utf-8-sig"))
    except json.JSONDecodeError as ex:
        refuse(f"ledger is not valid JSON ({ex}) — fix it by hand, then run tools/validate.py")
    if not isinstance(doc, dict):
        refuse("ledger must be a JSON object")
    doc.setdefault("entries", [])
    return doc

def main():
    p = argparse.ArgumentParser(epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("ledger")
    p.add_argument("--claim", required=True)
    p.add_argument("--falsifier", required=True)
    p.add_argument("--verify-by", required=True)
    p.add_argument("--track")
    p.add_argument("--stated-on", default=datetime.date.today().isoformat())
    a = p.parse_args()

    claim, falsifier = flat(a.claim), flat(a.falsifier)
    if len(claim) < 8: refuse("claim too short (schema minLength 8) — write one checkable sentence")
    if len(falsifier) < 8:
        refuse("falsifier too short (schema minLength 8) — write down what would prove you wrong (spec discipline 4)")
    stated = parse_date(a.stated_on, "--stated-on")
    verify = parse_date(a.verify_by, "--verify-by")
    if verify < stated: refuse("verify_by earlier than stated_on")
    track = flat(a.track) if a.track else ""
    if len(track) > 40: refuse("track longer than 40 chars (schema maxLength)")

    doc = load_ledger(a.ledger)
    year = stated.year
    prefix = f"J-{year}-"
    used = [int(m.group(1)) for e in doc["entries"]
            if isinstance(e, dict) and isinstance(e.get("id"), str)
            and (m := re.fullmatch(re.escape(prefix) + r"(\d{3})", e["id"]))]
    nnn = max(used, default=0) + 1
    if nnn > 999: refuse(f"id space exhausted for {year} (J-{year}-999 reached)")

    entry = {"id": f"{prefix}{nnn:03d}", "claim": claim, "falsifier": falsifier,
             "stated_on": stated.isoformat(), "verify_by": verify.isoformat(),
             "status": "pending"}
    if track: entry["track"] = track
    doc["entries"].append(entry)

    write_validated(a.ledger, doc)
    print("OK:", entry["id"])

def write_validated(path, doc):
    """Write to a temp file, validate it, then atomically replace the ledger."""
    d = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
            f.write("\n")
        v = os.path.join(os.path.dirname(os.path.abspath(__file__)), "validate.py")
        r = subprocess.run([sys.executable, v, tmp], capture_output=True, text=True)
        if r.returncode != 0:
            sys.stdout.write(r.stdout)
            refuse("result does not conform — ledger left untouched")
        if os.path.isfile(path):  # keep the owner's chosen permissions; fresh ledgers stay private 0600
            os.chmod(tmp, os.stat(path).st_mode & 0o7777)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

if __name__ == "__main__":
    main()
