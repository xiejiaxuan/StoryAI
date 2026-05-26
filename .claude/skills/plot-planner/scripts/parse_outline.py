#!/usr/bin/env python3
"""
parse_outline.py — 从小说大纲解析出逐章写作指令

支持三种格式:
  纯文本: 按"第X章"分隔
  JSON: {"chapters": {"1": {"title": "...", "plot": "..."}}}
  Markdown: # 第X章

用法:
  python parse_outline.py --outline <大纲文件> --output <输出目录>
  python parse_outline.py --outline <大纲文件> --output <输出目录> --json chapters.json
"""
import argparse
import json
import os
import re
import sys


HARD_CONSTRAINTS = """## 硬性约束
1. **纯中文**：所有数字用中文写法（一、二、三十），零阿拉伯数字，零英文
2. **零 AI 标记**：禁止"暗思涌起""心理描写""命运的齿轮""心中涌起"等 AI 标记词
3. **禁止模板结尾**：禁止"真正的危机才刚刚开始""未完待续""更大的风暴即将来临"
4. **忠于大纲**：不自由发挥核心剧情，不跳过大纲指定的情节节点
5. **直接输出正文**：不要说明文字、不要前言、不要后记"""


def parse_text(text):
    """纯文本大纲解析。"""
    chs, cur, title, plot = {}, None, "", []
    for line in text.split('\n'):
        line = line.strip()
        m = re.match(r'(?:第|Chapter\s+)(\d+)[章节回]*(?:[：:\s]+(.*))?', line, re.IGNORECASE)
        if m:
            if cur and plot:
                chs[cur] = {"title": title, "plot": '\n'.join(plot)}
            cur = int(m.group(1))
            title = m.group(2) or f"第{cur}章"
            plot = []
        elif cur and line:
            plot.append(line)
    if cur and plot:
        chs[cur] = {"title": title, "plot": '\n'.join(plot)}
    return chs


def parse_markdown(text):
    """Markdown 大纲解析。"""
    return parse_text(text)


def parse_json_outline(text):
    """JSON 大纲解析。"""
    data = json.loads(text)
    src = data.get("chapters", data.get("volume", data))
    r = {}
    for k, v in src.items():
        try:
            key = int(k)
            r[key] = v if isinstance(v, dict) else {"title": str(v), "plot": ""}
        except (ValueError, TypeError):
            pass
    return r


def detect_format(text):
    t = text.strip()
    if t.startswith('{') or t.startswith('['):
        return "json"
    if re.search(r'^#{1,3}\s+(?:第|Chapter)', t, re.MULTILINE):
        return "markdown"
    return "text"


def make_prompt(ch_num, info, prev_chapter_summary="", world_summary="", character_context=""):
    """生成单章写作指令。"""
    title = info.get("title", f"第{ch_num}章")
    plot = info.get("plot", "")

    parts = [
        f"# 第{ch_num}章写作指令：{title}",
        "",
    ]

    if world_summary:
        parts.append(f"## 世界观上下文\n{world_summary}\n")

    if character_context:
        parts.append(f"## 相关角色\n{character_context}\n")

    if plot:
        parts.append(f"## 本章剧情\n{plot}\n")
    else:
        parts.append(f"## 本章剧情\n（无大纲指定剧情，根据前章自然续写）\n")

    if prev_chapter_summary:
        parts.append(f"## 前章摘要\n{prev_chapter_summary}\n")

    parts.append(HARD_CONSTRAINTS)

    return '\n'.join(parts)


def main():
    ap = argparse.ArgumentParser(description="从大纲生成逐章写作指令")
    ap.add_argument("--outline", required=True, help="大纲文件路径")
    ap.add_argument("--output", required=True, help="输出目录")
    ap.add_argument("--context", help="上下文 JSON（含 world_summary, character_context）")
    ap.add_argument("--prev-chapter", help="前一章摘要文本")
    args = ap.parse_args()

    with open(args.outline, 'r', encoding='utf-8') as f:
        text = f.read()

    fmt = detect_format(text)
    if fmt == "json":
        chs = parse_json_outline(text)
    else:
        chs = parse_text(text)

    if not chs:
        print("错误: 解析到 0 个章节，请检查大纲格式")
        sys.exit(1)

    print(f"解析 {len(chs)} 个章节（格式: {fmt}）")

    # 加载上下文
    world_summary = ""
    character_context = ""
    prev_summary = ""
    if args.context and os.path.exists(args.context):
        with open(args.context, 'r', encoding='utf-8') as f:
            ctx = json.load(f)
        world_summary = ctx.get("world_summary", "")
        character_context = ctx.get("character_context", "")
    if args.prev_chapter and os.path.exists(args.prev_chapter):
        with open(args.prev_chapter, 'r', encoding='utf-8') as f:
            prev_summary = f.read()[-500:]

    os.makedirs(args.output, exist_ok=True)

    briefs = {}
    for num in sorted(chs.keys()):
        info = chs[num]
        prompt = make_prompt(num, info, prev_summary, world_summary, character_context)
        fname = f"{num:04d}.md"
        fname_safe = re.sub(r'[<>:"/\\|?*]', '_', fname)
        out_path = os.path.join(args.output, fname_safe)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(prompt)
        print(f"  {fname_safe}")
        briefs[str(num)] = {"title": info.get("title", ""), "plot": info.get("plot", "")}

    # 保存章节摘要 JSON
    chapters_json_path = os.path.join(args.output, "chapter_briefs.json")
    with open(chapters_json_path, 'w', encoding='utf-8') as f:
        json.dump({
            "format_version": "1.0",
            "chapter_count": len(briefs),
            "chapters": briefs,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n完成: {len(briefs)} 个写作指令 + chapter_briefs.json")


if __name__ == "__main__":
    main()
