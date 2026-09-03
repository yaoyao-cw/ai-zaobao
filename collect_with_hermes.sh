#!/usr/bin/env bash
set -euo pipefail
# Collect today's AI briefing via Hermes Agent (xAI SuperGrok OAuth, not Grok Bot quota).
ROOT=/workspace/ai-briefing
DATE="$(TZ=Asia/Shanghai date +%F)"
OUT="$ROOT/data/${DATE}.json"
export HERMES_ACCEPT_HOOKS=1
export TZ=Asia/Shanghai
mkdir -p "$ROOT/data" "$ROOT/logs"
LOG="$ROOT/logs/hermes-collect-${DATE}.log"

echo "[collect] date=$DATE via hermes $(command -v hermes)" | tee "$LOG"

set +e
hermes chat --oneshot -Q --yolo \
  --in "$ROOT" \
  --query-file "$ROOT/HERMES_COLLECT.md" \
  --max-turns 180 \
  --run-budget 1800 \
  >>"$LOG" 2>&1
code=$?
set -e

if [[ ! -f "$OUT" ]]; then
  echo "[collect] FAIL: missing $OUT (hermes exit $code)" | tee -a "$LOG"
  exit 2
fi

python3 "$ROOT/collect_xhs_public.py" >>"$LOG" 2>&1 || echo "[collect] xhs public skipped" | tee -a "$LOG"
python3 "$ROOT/collect_github_search.py" >>"$LOG" 2>&1 || echo "[collect] github search skipped" | tee -a "$LOG"
python3 "$ROOT/collect_papers.py" >>"$LOG" 2>&1 || echo "[collect] papers skipped" | tee -a "$LOG"
python3 "$ROOT/collect_metrics.py" >>"$LOG" 2>&1 || echo "[collect] metrics overlay skipped" | tee -a "$LOG"
python3 "$ROOT/collect_x_follows.py" >>"$LOG" 2>&1 || echo "[collect] x follows skipped" | tee -a "$LOG"

python3 - "$OUT" << 'PY'
import json, sys
p = sys.argv[1]
d = json.load(open(p, encoding="utf-8"))
items = d.get("items") or []
assert d.get("date"), "missing date"
assert isinstance(items, list) and 80 <= len(items) <= 260, f"bad item count {len(items)}"
for i, it in enumerate(items, 1):
    href = it.get("href") or ""
    assert href.startswith("http"), f"item {i} bad href"
feat = sum(1 for i in items if i.get("featured") or int(str(i.get("rank") or "99") or "99") <= 36)
print(f"[collect] ok {d['date']} items={len(items)} featured={feat} lede={d.get('lede','')[:80]}")
PY

exit "$code"
