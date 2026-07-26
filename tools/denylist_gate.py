#!/usr/bin/env python3
"""Generic denylist gate: scan files for lines matching YOUR private blocklist.

Usage:
  GUARD_BLOCKLIST=/path/to/blocklist.txt python3 tools/denylist_gate.py FILE [FILE...]
  python3 tools/denylist_gate.py --blocklist PATH FILE [FILE...]

Blocklist format: one regular expression per line; blank lines and #comments ignored.
Fail-closed semantics:
  * blocklist path given but missing/empty  -> exit 1 (refuse to pass)
  * any match                              -> exit 1
Output on hit: file:line:pattern-index only. Content is NOT echoed unless
--show-match is passed (never enable it in CI on a public repository).
Bring your own blocklist. This repository ships only blocklist.example.txt;
a real blocklist is a sensitive asset and must live OUTSIDE version control.
"""
import os, re, sys

def load_patterns(path):
    if not path or not os.path.isfile(path):
        print("FAIL: blocklist not found:", path); sys.exit(1)
    pats = []
    for ln in open(path, encoding="utf-8"):
        ln = ln.strip()
        if ln and not ln.startswith("#"):
            pats.append(re.compile(ln))
    if not pats:
        print("FAIL: blocklist is empty:", path); sys.exit(1)
    return pats

def main(argv):
    show = "--show-match" in argv
    argv = [a for a in argv if a != "--show-match"]
    if "--blocklist" in argv:
        i = argv.index("--blocklist"); bl = argv[i+1]; files = argv[1:i] + argv[i+2:]
    else:
        bl = os.environ.get("GUARD_BLOCKLIST"); files = argv[1:]
    pats = load_patterns(bl)
    hits = 0
    for f in files:
        try:
            lines = open(f, encoding="utf-8", errors="ignore").read().splitlines()
        except OSError:
            continue
        for n, line in enumerate(lines, 1):
            for pi, p in enumerate(pats):
                if p.search(line):
                    hits += 1
                    print(f"HIT: {f}:{n}:pattern#{pi}" + (f" :: {line.strip()[:120]}" if show else ""))
    if hits:
        print(f"FAIL: {hits} hit(s)"); return 1
    print("OK: clean"); return 0

if __name__ == "__main__":
    if len(sys.argv) < 2: print(__doc__); sys.exit(2)
    sys.exit(main(sys.argv))
