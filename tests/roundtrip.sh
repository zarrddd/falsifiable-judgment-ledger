#!/bin/bash
# Roundtrip acceptance: the full ledger loop must work end-to-end,
# and discipline violations must be refused. Pinned dates keep it deterministic.
set -euo pipefail
cd "$(dirname "$0")/.."
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
L="$TMP/ledger.json"

echo "--- 1. new_entry creates a ledger from nothing"
python3 tools/new_entry.py "$L" \
  --claim "示例项目将在 2026-02-01 前发布 1.0。" \
  --falsifier "至 2026-02-01 官方仓库无 1.0 tag。" \
  --track "roundtrip" --stated-on 2026-01-01 --verify-by 2026-02-01
python3 tools/validate.py "$L"

echo "--- 2. second entry gets the next id"
python3 tools/new_entry.py "$L" \
  --claim "示例指标将在 2026-03-01 前高于 100。" \
  --falsifier "至 2026-03-01 官方口径读数不高于 100。" \
  --stated-on 2026-01-02 --verify-by 2026-03-01
grep -q '"J-2026-002"' "$L" || { echo "FAIL: expected J-2026-002"; exit 1; }
python3 tools/validate.py "$L"

echo "--- 3. discipline: empty/blank falsifier must be refused"
if python3 tools/new_entry.py "$L" --claim "一条长度足够的可检验判断。" --falsifier "  " \
     --stated-on 2026-01-03 --verify-by 2026-03-01 2>/dev/null; then
  echo "FAIL: empty falsifier accepted"; exit 1
fi

echo "--- 4. discipline: verify_by before stated_on must be refused"
if python3 tools/new_entry.py "$L" --claim "一条长度足够的可检验判断。" \
     --falsifier "一条长度足够的证伪条件。" \
     --stated-on 2026-01-03 --verify-by 2026-01-02 2>/dev/null; then
  echo "FAIL: verify_by earlier than stated_on accepted"; exit 1
fi

echo "--- 5. discipline: judging before expiry must be refused"
if python3 tools/resolve.py "$L" --id J-2026-001 --status correct \
     --note "early" --on 2026-01-15 2>/dev/null; then
  echo "FAIL: early adjudication accepted"; exit 1
fi

echo "--- 6. judging on the expiry date works"
python3 tools/resolve.py "$L" --id J-2026-001 --status wrong \
  --note "到期核对：无 1.0 tag。判错，原文照登。" --on 2026-02-01
python3 tools/validate.py "$L"

echo "--- 7. discipline: an adjudicated entry cannot be re-judged"
if python3 tools/resolve.py "$L" --id J-2026-001 --status correct \
     --note "flip" --on 2026-02-02 2>/dev/null; then
  echo "FAIL: re-adjudication accepted"; exit 1
fi

echo "--- 8. expiry_check flags the still-pending entry after its date"
if python3 tools/expiry_check.py "$L" --as-of 2026-04-01 >/dev/null; then
  echo "FAIL: overdue entry not flagged"; exit 1
fi
python3 tools/expiry_check.py "$L" --as-of 2026-02-15

echo "--- 9. report: counts and markdown render"
OUT="$(python3 tools/report.py "$L" --as-of 2026-02-15)"
echo "$OUT" | grep -q "entries: 2"        || { echo "FAIL: total";  exit 1; }
echo "$OUT" | grep -q "pending: 1"        || { echo "FAIL: pending"; exit 1; }
echo "$OUT" | grep -q "wrong: 1"          || { echo "FAIL: wrong";  exit 1; }
python3 tools/report.py "$L" --as-of 2026-02-15 --md | grep -q "J-2026-001" \
  || { echo "FAIL: md render"; exit 1; }

echo "--- 10. validate.py negative coverage: a gutted validator must not pass this suite"
BAD="$TMP/bad.json"
python3 - "$L" "$BAD" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1]))
doc["entries"][0]["private_note"] = "leak"          # unknown field (discipline 7)
json.dump(doc, open(sys.argv[2], "w"), ensure_ascii=False)
PY
if python3 tools/validate.py "$BAD" >/dev/null 2>&1; then
  echo "FAIL: unknown field accepted (structural closure broken)"; exit 1
fi
python3 - "$L" "$BAD" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1]))
doc["entries"].append(dict(doc["entries"][0]))       # duplicate id
json.dump(doc, open(sys.argv[2], "w"), ensure_ascii=False)
PY
if python3 tools/validate.py "$BAD" >/dev/null 2>&1; then
  echo "FAIL: duplicate id accepted"; exit 1
fi
python3 - "$L" "$BAD" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1]))
doc["entries"][0]["claim"] = "太短"                  # violates schema minLength 8
json.dump(doc, open(sys.argv[2], "w"), ensure_ascii=False)
PY
if python3 tools/validate.py "$BAD" >/dev/null 2>&1; then
  echo "FAIL: sub-minLength claim accepted (validator weaker than schema)"; exit 1
fi

echo "--- 11. discipline: blank resolution note must be refused"
if python3 tools/resolve.py "$L" --id J-2026-002 --status partial \
     --note "   " --on 2026-03-01 2>/dev/null; then
  echo "FAIL: blank resolution note accepted"; exit 1
fi

echo "--- 12. discipline: a future --on (postdated verdict) must be refused"
if python3 tools/resolve.py "$L" --id J-2026-002 --status correct \
     --note "postdate attempt" --on 2999-01-01 2>/dev/null; then
  echo "FAIL: postdated verdict accepted"; exit 1
fi

echo "--- 13. first-run UX: missing ledger fails with a message, not a traceback"
for t in "tools/expiry_check.py" "tools/report.py"; do
  OUT="$(python3 $t "$TMP/nope.json" 2>&1)" && { echo "FAIL: $t exit 0 on missing file"; exit 1; }
  echo "$OUT" | grep -q "Traceback" && { echo "FAIL: $t tracebacks on missing file"; exit 1; }
done

echo "--- 14. hostile text: CR/pipe in a claim cannot break the --md table"
python3 tools/new_entry.py "$L" \
  --claim "$(printf '从 Word 粘贴的判断 | 含竖线\r\n与回车，长度足够。')" \
  --falsifier "到期时按官方口径核对不成立即算错。" \
  --stated-on 2026-01-04 --verify-by 2026-06-01
ROWS="$(python3 tools/report.py "$L" --as-of 2026-02-15 --md | grep -c '^| J-')"
[ "$ROWS" -eq 3 ] || { echo "FAIL: md table has $ROWS data rows, expected 3 (breakout?)"; exit 1; }

echo "--- 15. demo ledger still conforms (nothing regressed)"
python3 tools/validate.py demo/demo-ledger.json
python3 tools/expiry_check.py demo/demo-ledger.json --as-of 2026-07-01

echo "ROUNDTRIP OK"
