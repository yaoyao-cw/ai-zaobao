# 非 X 雷达加厚（2026-09-03）

## 目标与现状

| 雷达 | 本轮后 | 做法 |
| GitHub | 滚动库存 ~300 质量仓（不当天推倒） | trending ∪ search(stars≥10) ∪ 前几天。硬件 watch 不过度放 0 star。 |
| YouTube | 当天/近窗 30+，有播放量 | RSS Atom；views 走 media:community/statistics；补 unitree/Boston Dynamics/ollama 等 handle。 |
| 论文 | 日 40–80 | HF daily_papers + papers.cool cs.CV/RO/AI，不倒 arXiv 全量。 |
| 小红书 | 有就展示，不造假 | 搜索页登录墙。Bing/DDG 不给 explore 直链。公开账号 watch + 浏览器搜原帖。穿搭过滤。自媒体/ESP32 算 AI。 |
| 资讯 | 官方 RSS 即可 | 不靠微信公众号。 |

## 8:00 采集顺序（Hermes 之后）

1. collect_xhs_public.py
2. collect_github_search.py
3. collect_papers.py
4. collect_metrics.py（YouTube + overlay）
5. collect_x_follows.py
6. render + wrangler pages deploy

## 不要做

- 不买 X API credits
- 不造假小红书笔记
- 不加国内微信公众号
- GitHub search 0 star 噪音不进雷达
