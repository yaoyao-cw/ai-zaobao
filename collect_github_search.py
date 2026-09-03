#!/usr/bin/env python3
"""Append recently-updated AI/hardware repos into the rolling GitHub corpus."""
from __future__ import annotations
import json, ssl, time, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
sys.path.insert(0, "/workspace/ai-briefing")
from classify import apply_two_tier

ROOT = Path("/workspace/ai-briefing")
DATA = ROOT / "data"
SH = timezone(timedelta(hours=8))
TODAY = datetime.now(SH).strftime("%Y-%m-%d")
UA = "ai-zaobao (https://ai-zaobao.pages.dev/)"
CTX = ssl.create_default_context()
QUERIES = [
    "esp32 AI OR llm OR agent",
    "mcp server stars:>10",
    "comfyui stars:>20",
    "xiaohongshu OR jimeng",
    "papermono OR mosaico OR folotoy OR m5stack",
    "llm agent stars:>20 pushed:>2026-07-01",
    "esp32 llm OR whisper OR llama",
    "openclaw OR esp-claw",
    "digital human stars:>5",
]


def http_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20, context=CTX) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8", "replace"))
        except Exception:
            body = {}
        return e.code, body
    except Exception as e:
        return 0, {"error": str(e)}


def main():
    path = DATA / "github-corpus.json"
    corpus = {"updated": TODAY, "note": "rolling github", "items": []}
    if path.exists():
        try:
            corpus = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    items = corpus.get("items") or []
    by = {(it.get("href") or "").split("?")[0]: it for it in items}
    old = len(by)
    added = 0
    for q in QUERIES:
        url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode({
            "q": q, "sort": "updated", "order": "desc", "per_page": "30",
        })
        code, data = http_json(url)
        print(f"  search {q!r} http={code} n={len(data.get('items') or [])}", flush=True)
        if code == 403:
            break
        for repo in data.get("items") or []:
            href = (repo.get("html_url") or "").split("?")[0]
            if not href or href in by:
                continue
            stars = int(repo.get("stargazers_count") or 0)
            name = (repo.get("full_name") or "").lower()
            watch = any(w in name for w in ("papermono","mosaico","folotoy","ai-passport","esp-claw","openclaw","m5stack"))
            if stars < 10 and not watch:
                continue
            it = {
                "channel": "github",
                "cat": "dev",
                "source": "GitHub search",
                "href": href,
                "title": repo.get("full_name") or repo.get("name") or href,
                "desc": (repo.get("description") or "")[:220],
                "why": f"GitHub 搜索「{q}」，最近有推送。",
                "meta": "github.com",
                "pub": repo.get("pushed_at") or TODAY,
                "added": TODAY,
                "stars": int(repo.get("stargazers_count") or 0),
                "heat": int(repo.get("stargazers_count") or 0),
                "featured": False,
            }
            apply_two_tier(it)
            by[href] = it
            added += 1
        time.sleep(0.8)
    items = list(by.values())
    corpus = {
        "updated": TODAY,
        "date": TODAY,
        "note": "rolling GitHub corpus: trending ∪ search ∪ previous days",
        "n": len(items),
        "items": items,
    }
    path.write_text(json.dumps(corpus, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"github-corpus old={old} added={added} now={len(items)}", flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
