#!/usr/bin/env python3
"""format_converter.py — 大纲格式互转（纯文本 ↔ JSON ↔ Markdown）"""

import json
import re


# ============================================================
# 解析：文本 → dict
# ============================================================

def parse_text_outline(text):
    """从纯文本大纲解析章节。按"第X章"分隔，提取标题和剧情。"""
    chapters = {}
    cur, title, plot = None, "", []
    for line in text.split('\n'):
        line = line.strip()
        m = re.match(r'(?:第|Chapter\s+)(\d+)[章节回]*(?:[：:\s]+(.*))?', line, re.IGNORECASE)
        if m:
            if cur and plot:
                chapters[cur] = {"title": title, "plot": '\n'.join(plot)}
            cur = int(m.group(1))
            title = m.group(2) or f"第{cur}章"
            plot = []
        elif cur and line:
            plot.append(line)
    if cur and plot:
        chapters[cur] = {"title": title, "plot": '\n'.join(plot)}
    return chapters


def parse_markdown_outline(text):
    """从 Markdown 大纲解析章节。按 # 标题分隔。"""
    chapters = {}
    cur, title, plot = None, "", []
    for line in text.split('\n'):
        line = line.strip()
        m = re.match(r'^#{1,3}\s+(?:第|Chapter\s+)?(\d+)[章节回]*(?:[：:\s]+(.*))?', line, re.IGNORECASE)
        if m:
            if cur and plot:
                chapters[cur] = {"title": title, "plot": '\n'.join(plot)}
            cur = int(m.group(1))
            title = m.group(2) or f"第{cur}章"
            plot = []
        elif cur and line:
            plot.append(line)
    if cur and plot:
        chapters[cur] = {"title": title, "plot": '\n'.join(plot)}
    return chapters


def parse_json_outline(text):
    """从 JSON 大纲解析章节。"""
    data = json.loads(text)
    src = data.get("chapters", data.get("volume", data))
    chapters = {}
    for k, v in src.items():
        try:
            ch_num = int(k)
            if isinstance(v, dict):
                chapters[ch_num] = v
            else:
                chapters[ch_num] = {"title": str(v), "plot": ""}
        except (ValueError, TypeError):
            pass
    return chapters


# ============================================================
# 检测格式
# ============================================================

def detect_format(text):
    """自动检测大纲格式。返回 "json" | "markdown" | "text"。"""
    if text.strip().startswith('{') or text.strip().startswith('['):
        return "json"
    if re.search(r'^#{1,3}\s+(?:第|Chapter)', text, re.MULTILINE):
        return "markdown"
    return "text"


# ============================================================
# 统一入口
# ============================================================

def parse_outline(text_or_filepath):
    """统一大纲解析入口。自动检测格式。返回 {ch_num: {title, plot}}。"""
    # 判断是文件路径还是文本
    if '\n' not in text_or_filepath and len(text_or_filepath) < 500:
        try:
            with open(text_or_filepath, 'r', encoding='utf-8') as f:
                text = f.read()
        except (FileNotFoundError, OSError):
            text = text_or_filepath
    else:
        text = text_or_filepath

    fmt = detect_format(text)
    if fmt == "json":
        return parse_json_outline(text)
    elif fmt == "markdown":
        return parse_markdown_outline(text)
    else:
        return parse_text_outline(text)


# ============================================================
# 输出：dict → 各种格式
# ============================================================

def to_json(chapters, output_path=None):
    """将章节 dict 输出为 chapters.json。"""
    data = {
        "format_version": "1.0",
        "chapter_count": len(chapters),
        "chapters": {str(k): v for k, v in sorted(chapters.items())},
    }
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return json.dumps(data, ensure_ascii=False, indent=2)


def to_markdown(chapters, output_path=None):
    """将章节 dict 输出为 Markdown 大纲。"""
    lines = ["# 小说大纲\n"]
    for num in sorted(chapters.keys()):
        info = chapters[num]
        title = info.get("title", f"第{num}章")
        plot = info.get("plot", "")
        lines.append(f"## 第{num}章：{title}")
        if plot:
            lines.append(f"\n{plot}\n")
    text = '\n'.join(lines)
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
    return text
