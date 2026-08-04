"""
热点采集器 — 多源热搜聚合
============================
从微博、知乎、B站、百度、抖音等平台采集实时热点，
输出标准化 JSON 供 AI 分析。

运行方式：
  python collect_hotspots.py           # 采集所有源
  python collect_hotspots.py --source weibo  # 单源采集

输出：
  data/hotspots_YYYYMMDD_HHMMSS.json
"""

import json, os, sys, re, time, hashlib
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import quote

# ── 配置 ──────────────────────────────────────────────
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
BEIJING_TZ = timezone(timedelta(hours=8))
REQUEST_TIMEOUT = 15

HEADERS_MOBILE = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                  "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
}
HEADERS_PC = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Referer": "https://weibo.com/"
}
HEADERS_BILIBILI = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/"
}


# ── 工具函数 ──────────────────────────────────────────
def safe_fetch(url, headers=None, timeout=REQUEST_TIMEOUT, max_retries=2):
    """带重试的 HTTP GET，返回 (status, body_text)"""
    headers = headers or HEADERS_PC
    for attempt in range(max_retries + 1):
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                return resp.status, body
        except (URLError, HTTPError, OSError) as e:
            if attempt < max_retries:
                time.sleep(1 * (attempt + 1))
            else:
                return None, str(e)
    return None, "unknown error"


def normalize_topic(raw_text, source):
    """清洗话题文本，去掉 emoji 和来源标记"""
    text = raw_text.strip()
    # 去掉常见来源标记
    text = re.sub(r'\s*🔥|\s*📈|\s*📉|\s*🆕|\s*♨️', '', text)
    # 去掉微博热搜后面的数字标记
    text = re.sub(r'\s+\d+万?$', '', text)
    return text


def make_item(source, title, url="", heat="", rank=0, extra=None):
    """构造标准热点条目"""
    item = {
        "source": source,
        "title": normalize_topic(title, source),
        "url": url,
        "heat": str(heat) if heat else "",
        "rank": rank,
        "collected_at": datetime.now(BEIJING_TZ).isoformat(),
    }
    if extra:
        item["extra"] = extra
    return item


# ── 各平台采集器 ──────────────────────────────────────

def fetch_weibo():
    """微博热搜榜 — https://weibo.com/ajax/side/hotSearch"""
    url = "https://weibo.com/ajax/side/hotSearch"
    status, body = safe_fetch(url, headers=HEADERS_PC)
    if status != 200:
        print(f"[weibo] 请求失败: {body}")
        return []

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        print(f"[weibo] JSON 解析失败")
        return []

    items = []
    realtime = data.get("data", {}).get("realtime", [])
    for i, entry in enumerate(realtime[:30]):  # 取前30条
        word = entry.get("word", "")
        raw = entry.get("raw_hot", 0)
        url_scheme = entry.get("word_scheme", "")
        url_full = f"https://s.weibo.com/weibo?q={quote(word)}" if not url_scheme else url_scheme
        items.append(make_item("微博热搜", word, url_full, heat=raw, rank=i+1,
                               extra={"category": entry.get("category", "")}))
    print(f"[weibo] 采集 {len(items)} 条")
    return items


def fetch_zhihu():
    """知乎热榜 — https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total"""
    url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=30"
    status, body = safe_fetch(url, headers=HEADERS_MOBILE)
    if status != 200:
        # 知乎 API 可能限频，降级到 RSS
        print(f"[zhihu] API 失败 ({status})，尝试 RSS 降级")
        return fetch_zhihu_rss()

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        print(f"[zhihu] JSON 解析失败")
        return []

    items = []
    hot_list = data.get("data", [])
    for i, entry in enumerate(hot_list):
        target = entry.get("target", {})
        title = target.get("title", "")
        qid = target.get("id", "")
        url_full = f"https://www.zhihu.com/question/{qid}" if qid else ""
        detail = target.get("excerpt", "")[:200] if target.get("excerpt") else ""
        items.append(make_item("知乎热榜", title, url_full,
                               heat=target.get("follower_count", ""), rank=i+1,
                               extra={"excerpt": detail}))
    print(f"[zhihu] 采集 {len(items)} 条")
    return items


def fetch_zhihu_rss():
    """知乎热榜 RSS 降级方案"""
    url = "https://www.zhihu.com/rss"
    status, body = safe_fetch(url, headers=HEADERS_PC)
    if status != 200:
        print(f"[zhihu-rss] 不可用: {body}")
        return []

    import xml.etree.ElementTree as ET
    items = []
    try:
        root = ET.fromstring(body)
        for i, item in enumerate(root.iter("item")[:20]):
            title = item.find("title")
            link = item.find("link")
            if title is not None:
                items.append(make_item("知乎热榜", title.text or "",
                                       url=link.text if link is not None else "",
                                       rank=i+1))
    except ET.ParseError:
        print("[zhihu-rss] XML 解析失败")
        return []
    print(f"[zhihu-rss] 采集 {len(items)} 条")
    return items


def fetch_bilibili():
    """B站热门 — https://api.bilibili.com/x/web-interface/popular"""
    url = "https://api.bilibili.com/x/web-interface/popular?ps=30"
    status, body = safe_fetch(url, headers=HEADERS_BILIBILI)
    if status != 200:
        print(f"[bilibili] 请求失败: {body}")
        return []

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        print("[bilibili] JSON 解析失败")
        return []

    items = []
    videos = data.get("data", {}).get("list", [])
    for i, v in enumerate(videos):
        title = v.get("title", "")
        bvid = v.get("bvid", "")
        url_full = f"https://www.bilibili.com/video/{bvid}" if bvid else ""
        stat = v.get("stat", {})
        heat_info = f"播放:{stat.get('view',0)} 弹幕:{stat.get('danmaku',0)}"
        items.append(make_item("B站热门", title, url_full, heat=heat_info, rank=i+1,
                               extra={
                                   "author": v.get("owner", {}).get("name", ""),
                                   "desc": (v.get("desc", "") or "")[:150],
                                   "tname": v.get("tname", "")
                               }))
    print(f"[bilibili] 采集 {len(items)} 条")
    return items


def fetch_baidu():
    """百度热搜 — https://top.baidu.com/board?tab=realtime"""
    url = "https://top.baidu.com/board?tab=realtime"
    status, body = safe_fetch(url, headers=HEADERS_PC)
    if status != 200:
        print(f"[baidu] 请求失败: {body}")
        return []

    # 百度页面是 HTML，从中提取 JSON 数据
    items = []
    # 尝试匹配页面中的热榜 JSON
    json_match = re.search(r'<!--s-data:(.*?)-->', body, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            cards = data.get("data", {}).get("cards", [])
            for card in cards:
                for content in card.get("content", []):
                    title = content.get("word", "") or content.get("query", "")
                    desc = content.get("desc", "")
                    url_full = content.get("url", "") or content.get("rawUrl", "")
                    heat = content.get("hotScore", "") or content.get("heat_score", "")
                    if title:
                        items.append(make_item("百度热搜", title, url_full, heat=heat,
                                               rank=len(items)+1,
                                               extra={"desc": desc}))
            print(f"[baidu] 采集 {len(items)} 条 (JSON)")
            return items
        except (json.JSONDecodeError, KeyError):
            pass

    # 降级：正则从 HTML 提取
    titles = re.findall(r'<div class="c-single-text-ellipsis">(.*?)</div>', body)
    for i, t in enumerate(titles[:30]):
        clean = re.sub(r'<[^>]+>', '', t).strip()
        if clean and len(clean) > 1:
            items.append(make_item("百度热搜", clean, rank=i+1))
    print(f"[baidu] 采集 {len(items)} 条 (HTML regex)")
    return items


def fetch_douyin_proxy():
    """
    抖音热点 — 通过第三方站点间接采集
    抖音官方 API 需要 cookie/token，这里使用 tophub.today 作为聚合代理
    """
    url = "https://api.tophub.today/api/GetAllInfoGzip?id=DouyinHot&page=1"
    status, body = safe_fetch(url, headers=HEADERS_PC)
    if status != 200:
        print(f"[douyin] 代理失败: {body}")
        return []

    items = []
    try:
        data = json.loads(body)
        entries = data.get("Data", {}).get("data", [])
        for i, e in enumerate(entries[:20]):
            items.append(make_item("抖音热点", e.get("Title", ""),
                                   url=e.get("Url", ""),
                                   heat=e.get("desc", ""), rank=i+1))
    except (json.JSONDecodeError, KeyError):
        pass
    print(f"[douyin] 采集 {len(items)} 条")
    return items


def fetch_toutiao():
    """今日头条热榜 — 通过 tophub 聚合"""
    url = "https://api.tophub.today/api/GetAllInfoGzip?id=ToutiaoHot&page=1"
    status, body = safe_fetch(url, headers=HEADERS_PC)
    if status != 200:
        print(f"[toutiao] 代理失败: {body}")
        return []

    items = []
    try:
        data = json.loads(body)
        entries = data.get("Data", {}).get("data", [])
        for i, e in enumerate(entries[:20]):
            items.append(make_item("今日头条", e.get("Title", ""),
                                   url=e.get("Url", ""),
                                   heat=e.get("desc", ""), rank=i+1))
    except (json.JSONDecodeError, KeyError):
        pass
    print(f"[toutiao] 采集 {len(items)} 条")
    return items


# ── 汇总 ──────────────────────────────────────────────

ALL_SOURCES = {
    "weibo":    ("微博热搜", fetch_weibo),
    "zhihu":    ("知乎热榜", fetch_zhihu),
    "bilibili": ("B站热门", fetch_bilibili),
    "baidu":    ("百度热搜", fetch_baidu),
    "douyin":   ("抖音热点", fetch_douyin_proxy),
    "toutiao":  ("今日头条", fetch_toutiao),
}


def collect_all(sources=None):
    """采集指定源（默认全部），返回标准化热点列表"""
    source_keys = sources or list(ALL_SOURCES.keys())
    all_items = []
    stats = {}

    for key in source_keys:
        if key not in ALL_SOURCES:
            print(f"[skip] 未知数据源: {key}")
            continue
        name, fetcher = ALL_SOURCES[key]
        try:
            items = fetcher()
            all_items.extend(items)
            stats[name] = len(items)
        except Exception as e:
            print(f"[error] {name}: {e}")
            stats[name] = 0

    # 去重（按 title 相似度）
    deduped = deduplicate(all_items)

    return deduped, stats


def deduplicate(items, threshold=0.85):
    """简单的标题去重：完全相同 or 包含关系"""
    seen = []
    result = []
    for item in items:
        t = item["title"].strip()
        is_dup = False
        for s in seen:
            if t == s or (len(t) > 2 and (t in s or s in t)):
                is_dup = True
                break
        if not is_dup:
            seen.append(t)
            result.append(item)
    return result


def save_hotspots(items, stats):
    """保存热点到 JSON 文件"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now(BEIJING_TZ).strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(OUTPUT_DIR, f"hotspots_{timestamp}.json")

    output = {
        "meta": {
            "collected_at": datetime.now(BEIJING_TZ).isoformat(),
            "total_items": len(items),
            "source_stats": stats,
            "version": "1.0"
        },
        "items": items
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 同时写到 latest.json 方便后续读取
    latest_path = os.path.join(OUTPUT_DIR, "latest.json")
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n[✓] 保存 {len(items)} 条热点 → {filepath}")
    return filepath


# ── 主入口 ────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="多源热搜热点采集器")
    parser.add_argument("--source", "-s", choices=list(ALL_SOURCES.keys()) + ["all"],
                        default="all", help="指定数据源 (默认: all)")
    parser.add_argument("--output", "-o", help="自定义输出路径")
    args = parser.parse_args()

    print("=" * 50)
    print("  热点采集器 — 多源热搜聚合")
    print(f"  时间: {datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    sources = list(ALL_SOURCES.keys()) if args.source == "all" else [args.source]
    items, stats = collect_all(sources)

    total = sum(stats.values())
    print(f"\n  总计: {total} 条 → 去重后 {len(items)} 条")
    print(f"  各源: {json.dumps(stats, ensure_ascii=False)}")

    filepath = save_hotspots(items, stats)
    print(f"\n  输出: {filepath}")
