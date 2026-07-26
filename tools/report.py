#!/usr/bin/env python3
"""Scoreboard: counts, rates, and an optional markdown render for publishing.

Usage: python3 tools/report.py <ledger.json> [--as-of YYYY-MM-DD] [--md]

Plain mode prints machine-greppable counts. --md renders the full ledger as a
markdown table — wrong entries included, that is the point. Rates are stated
two ways (partial counted for and against) so the reader picks the harsher one.
Exit 0 on any valid ledger regardless of its contents (reporting is not a
gate; gates are validate.py / expiry_check.py); exit 2 on malformed input.
Note: this tool does NOT certify conformance — that claim is earned by
validate.py and expiry_check.py both exiting 0 (SPEC §5).
"""
import datetime, json, os, re, sys

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def die(msg):
    print("FAIL:", msg); sys.exit(2)

def main(argv):
    args = argv[1:]
    md = "--md" in args
    args = [a for a in args if a != "--md"]
    as_of = datetime.date.today()
    if "--as-of" in args:
        i = args.index("--as-of")
        if i + 1 >= len(args): print(__doc__); sys.exit(2)
        if not DATE_RE.match(args[i+1]): die("--as-of must be ISO YYYY-MM-DD")
        try:
            as_of = datetime.date.fromisoformat(args[i+1])
        except ValueError:
            die(f"--as-of is not a real date: {args[i+1]}")
        args = args[:i] + args[i+2:]
    if len(args) != 1: print(__doc__); sys.exit(2)
    if not os.path.isfile(args[0]):
        die(f"ledger not found: {args[0]} (create one with tools/new_entry.py)")
    try:
        doc = json.load(open(args[0], encoding="utf-8-sig"))
    except json.JSONDecodeError as ex:
        die(f"ledger is not valid JSON ({ex})")
    if not isinstance(doc, dict): die("ledger must be a JSON object")
    es = doc.get("entries", [])

    n = {"pending": 0, "correct": 0, "partial": 0, "wrong": 0}
    overdue = 0
    try:
        for e in es:  # touch every field the render needs, so malformed input fails here, before any output
            if not (isinstance(e["id"], str) and isinstance(e["claim"], str)
                    and isinstance(e["falsifier"], str)
                    and isinstance(e["verify_by"], str) and DATE_RE.match(e["verify_by"])):
                raise TypeError
            n[e["status"]] += 1
            if e["status"] == "pending" and datetime.date.fromisoformat(e["verify_by"]) < as_of:
                overdue += 1
    except (KeyError, ValueError, TypeError):
        die("ledger is malformed — run tools/validate.py for details")
    judged = n["correct"] + n["partial"] + n["wrong"]
    strict = f"{n['correct']}/{judged}" if judged else "n/a"
    lenient = f"{n['correct'] + n['partial']}/{judged}" if judged else "n/a"

    if not md:
        print(f"entries: {len(es)}")
        print(f"pending: {n['pending']} (overdue: {overdue})")
        print(f"correct: {n['correct']}  partial: {n['partial']}  wrong: {n['wrong']}")
        print(f"hit rate strict (correct only): {strict}")
        print(f"hit rate lenient (partial counted): {lenient}")
        return

    badge = {"pending": "⏳ pending", "correct": "✅ correct",
             "partial": "◐ partial", "wrong": "❌ wrong"}
    print(f"# 判断台账 · Judgment Ledger")
    if doc.get("fictional"):
        print("\n> **FICTIONAL** — 本账本全部条目为虚构演示数据。")
    print(f"\n共 {len(es)} 条 · 已判 {judged}（对 {n['correct']} / 部分 {n['partial']} / 错 {n['wrong']}）"
          f" · 待判 {n['pending']}（逾期 {overdue}）"
          f" · 严格命中 {strict} · 宽口径 {lenient}\n")
    print("| ID | 判断 | 证伪条件 | 到期 | 结果 |")
    print("|---|---|---|---|---|")
    for e in sorted(es, key=lambda x: x["id"]):
        note = e.get("resolution_note", "")
        tail = f"<br>{cell(note)}" if isinstance(note, str) and note else ""
        print(f"| {e['id']} | {cell(e['claim'])} | {cell(e['falsifier'])} "
              f"| {e['verify_by']} | {badge[e['status']]}{tail} |")
    print(f"\n*Format: Falsifiable Judgment Ledger v0.1 · as of {as_of.isoformat()}*")

def cell(s):
    """Neutralize table breakout: backslash first, then pipes; all line breaks to spaces."""
    s = s.replace("\\", "\\\\").replace("|", "\\|")
    return re.sub("[\\r\\n\\u2028\\u2029]+", " ", s)

if __name__ == "__main__":
    main(sys.argv)
