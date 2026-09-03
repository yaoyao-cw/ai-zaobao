#!/usr/bin/env python3
"""HF daily papers + papers.cool cs.CV/RO/AI. No arXiv dump."""
from __future__ import annotations
import json, re, ssl, time, urllib.request
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
ABS_RE = re.compile(r"(?:arxiv\.org/abs/|huggingface\.co/papers/)(\d{4}\.\d{4,5})")


def http(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, str(e)


def mk(href, title, desc, source, pub):
    it = {
        "channel": "news", "cat": "research", "href": href,
        "title": (title or href)[:180], "desc": (desc or "")[:280],
        "source": source, "why": source, "meta": source,
        "pub": pub or TODAY, "added": TODAY, "featured": False,
    }
    apply_two_tier(it)
    return it


def from_hf():
    code, body = http("https://huggingface.co/api/daily_papers")
    print("hf daily", code, flush=True)
    if code != 200:
        return []
    try:
        rows = json.loads(body)
    except json.JSONDecodeError:
        return []
    out = []
    if isinstance(rows, dict):
        rows = rows.get("papers") or rows.get("items") or []
    for row in rows or []:
        paper = row.get("paper") if isinstance(row, dict) else None
        if not isinstance(paper, dict):
            paper = row if isinstance(row, dict) else {}
        pid = paper.get("id") or row.get("id") or ""
        title = paper.get("title") or row.get("title") or pid
        summary = paper.get("summary") or paper.get("abstract") or ""
        pub = row.get("publishedAt") or paper.get("publishedAt") or TODAY
        if isinstance(pub, str) and "T" in pub:
            pub = pub.replace("T", " ")[:19]
        href = f"https://huggingface.co/papers/{pid}" if pid else ""
        if not href:
            continue
        out.append(mk(href, title, summary, "HF daily papers", pub))
    return out


def from_cool(cat):
    code, html = http(f"https://papers.cool/arxiv/{cat}")
    print("papers.cool", cat, code, len(html), flush=True)
    if code != 200:
        return []
    ids = []
    for m in re.finditer(r'href="(?:https://arxiv.org/abs/|/arxiv/)(\d{4}\.\d{4,5})"', html):
        ids.append(m.group(1))
    if not ids:
        ids = ABS_RE.findall(html)
    seen = set(); out = []
    for pid in ids:
        if pid in seen:
            continue
        seen.add(pid)
        idx = html.find(pid)
        window = re.sub(r"<[^>]+>", " ", html[max(0, idx-200): idx+300])
        window = re.sub(r"\s+", " ", window).strip()
        title = window[:120] or pid
        href = f"https://arxiv.org/abs/{pid}"
        out.append(mk(href, title, window[:220], f"papers.cool {cat}", TODAY))
        if len(out) >= 16:
            break
    return out


def main():
    by = {}
    for it in from_hf() + from_cool("cs.CV") + from_cool("cs.RO") + from_cool("cs.AI"):
        href = (it.get("href") or "").split("?")[0]
        if href and href not in by:
            by[href] = it
        time.sleep(0.05)
    items = list(by.values())
    feed = {"date": TODAY, "n": len(items), "items": items,
            "note": "HF daily + papers.cool cs.CV/RO/AI, not full arXiv."}
    path = DATA / f"papers-feed-{TODAY}.json"
    path.write_text(json.dumps(feed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote", path, "n=", len(items), flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
