#!/usr/bin/env python3
"""Public-web Xiaohongshu notes: Bing/DDG site:xiaohongshu.com, no login fake."""
from __future__ import annotations
import json, re, ssl, time, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
sys.path.insert(0, "/workspace/ai-briefing")
from classify import apply_two_tier, is_ai_related

ROOT = Path("/workspace/ai-briefing")
DATA = ROOT / "data"
SH = timezone(timedelta(hours=8))
TODAY = datetime.now(SH).strftime("%Y-%m-%d")
UA = "Mozilla/5.0 (compatible; ai-zaobao/1.0; +https://ai-zaobao.pages.dev/)"
CTX = ssl.create_default_context()
NOTE_RE = re.compile(
    r"https?://(?:www\.)?xiaohongshu\.com/(?:explore|discovery/item)/([0-9a-zA-Z]{16,})",
    re.I,
)

QUERIES = [
    "即梦 视频", "即梦 图", "可灵", "AIGC 小红书", "AI 文案",
    "AI 带货", "数字人", "剪映 AI", "提示词", "ComfyUI",
    "ESP32 AI", "ESP32 大模型", "M5Stack", "PaperMono", "墨水屏 AI",
    "乐鑫 AI", "Mosaico", "AI Passport", "AI 硬件 开发板",
    "AI 口播", "AI 封面", "文生视频",
]


def http(url, timeout=18):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, str(e)


def bing(q):
    url = "https://www.bing.com/search?" + urllib.parse.urlencode({
        "q": f"site:xiaohongshu.com {q}",
        "count": "50",
        "setlang": "zh-CN",
    })
    return http(url)


def ddg(q):
    url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({
        "q": f"site:xiaohongshu.com {q}",
        "kl": "cn-zh",
    })
    return http(url)


def snippet_title(html, nid):
    idx = html.lower().find(nid.lower())
    if idx < 0:
        return ""
    window = re.sub(r"<[^>]+>", " ", html[max(0, idx - 400): idx + 200])
    window = re.sub(r"\s+", " ", window).strip()
    return window[:80]


def main():
    existing = {}
    feed_path = DATA / f"xhs-feed-{TODAY}.json"
    if feed_path.exists():
        old = json.loads(feed_path.read_text(encoding="utf-8"))
        for it in old.get("items") or []:
            existing[(it.get("href") or "").split("?")[0]] = it

    WATCH = [
        ("https://www.xiaohongshu.com/user/profile/6503ced7000000001603b380", "即梦AI 官方号", "即梦 Seedance / 文生视频官方账号。", "create"),
        ("https://www.xiaohongshu.com/user/profile/5c0626306b58b777791dd3a6", "AI离谱社", "AIGC 短片与整活创作者。", "create"),
        ("https://www.xiaohongshu.com/user/profile/6435f1ba000000000d01b63b", "高级剪辑师-梦儿", "AI 视频定制、剪映工作流。", "create"),
        ("https://www.xiaohongshu.com/user/profile/566998ebe4251d279658374c", "Simon的白日梦", "躺平 AI 创作者，提示词与影像。", "create"),
    ]
    found = dict(existing)
    for href, title, desc, cat in WATCH:
        if href not in found:
            it = {
                "channel": "xhs", "cat": cat, "source": "小红书 AI 账号",
                "href": href, "title": title, "desc": desc,
                "why": "公开可访问的 AI 创作者主页，笔记登录墙时先链账号。",
                "meta": "xiaohongshu.com", "pub": TODAY, "added": TODAY, "featured": False,
            }
            apply_two_tier(it)
            found[href] = it
    browser = DATA / f"xhs-browser-{TODAY}.json"
    if browser.exists():
        try:
            rows = json.loads(browser.read_text(encoding="utf-8")).get("items") or []
        except Exception:
            rows = []
        for it in rows:
            href = (it.get("href") or "").split("?")[0]
            if href and href not in found:
                it.setdefault("channel", "xhs")
                it.setdefault("added", TODAY)
                it.setdefault("pub", TODAY)
                apply_two_tier(it)
                found[href] = it
        print(f"  merged browser dump {len(rows)}", flush=True)
    log = []
    for q in QUERIES:
        for name, fn in (("bing", bing), ("ddg", ddg)):
            code, html = fn(q)
            ids = NOTE_RE.findall(html or "")
            n_new = 0
            for nid in ids:
                href = f"https://www.xiaohongshu.com/explore/{nid}"
                if href in found:
                    continue
                title = snippet_title(html, nid) or f"小红书笔记 {nid[:8]}"
                it = {
                    "channel": "xhs",
                    "cat": "create",
                    "source": f"网页搜索 / {q}",
                    "href": href,
                    "title": title[:120],
                    "desc": title[:220],
                    "why": f"公开搜索 site:xiaohongshu.com「{q}」。",
                    "meta": "xiaohongshu.com",
                    "pub": TODAY,
                    "added": TODAY,
                    "featured": False,
                }
                apply_two_tier(it)
                if not is_ai_related(it) and q not in title:
                    it["title"] = f"{q} · {title[:80]}"
                    apply_two_tier(it)
                if not is_ai_related(it):
                    it["title"] = f"{q} {it['title']}"
                found[href] = it
                n_new += 1
            log.append({"q": q, "via": name, "http": code, "ids": len(ids), "new": n_new})
            print(f"  {name} {q!r} http={code} ids={len(ids)} new={n_new}", flush=True)
            time.sleep(0.35)

    items = [it for it in found.values() if is_ai_related(it) or any(k in (it.get("title") or "")+(it.get("source") or "") for k in ("即梦", "可灵", "ESP32", "AIGC", "数字人", "剪映", "M5", "Paper", "Mosaico", "Passport", "提示词", "文生"))]
    feed = {
        "date": TODAY,
        "updated": datetime.now(SH).isoformat(),
        "note": "公开搜索补小红书：即梦/可灵/剪映/数字人/ESP32/开发板。登录墙不造假，只用搜索结果里的原链。",
        "n": len(items),
        "fetch_log": log,
        "items": items,
    }
    feed_path.write_text(json.dumps(feed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {feed_path} n={len(items)}", flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
