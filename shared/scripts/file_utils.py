#!/usr/bin/env python3
"""file_utils.py — 项目文件 I/O 与路径解析"""

import json
import os
import re
from pathlib import Path


def find_project_root(start_dir=None):
    """向上查找包含 .storyai/ 目录的项目根。"""
    d = Path(start_dir) if start_dir else Path.cwd()
    for p in [d, *d.parents]:
        if (p / ".storyai").is_dir():
            return str(p)
    return str(d)


def find_skill_dir():
    """查找 .claude/skills/ 目录的绝对路径。从当前脚本位置反推。"""
    script_dir = Path(__file__).resolve().parent
    for p in [script_dir, *script_dir.parents]:
        skills = p / ".claude" / "skills"
        if skills.is_dir():
            return str(skills)
    return None


def ensure_dir(path):
    """创建目录（如不存在）。"""
    Path(path).mkdir(parents=True, exist_ok=True)


def load_json(filepath):
    """读取 JSON 文件，失败返回 {}。"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_json(filepath, data, indent=2):
    """写入 JSON 文件，自动创建父目录。"""
    ensure_dir(os.path.dirname(filepath) or ".")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def load_text(filepath):
    """读取文本文件。"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def save_text(filepath, text):
    """写入文本文件，自动创建父目录。"""
    ensure_dir(os.path.dirname(filepath) or ".")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)


def find_chapter_files(project_root):
    """按序号列出 chapters/ 下的所有章节文件。"""
    chapters_dir = os.path.join(project_root, "chapters")
    if not os.path.isdir(chapters_dir):
        return []
    pattern = re.compile(r"chapter_(\d+)\.md$")
    files = []
    for f in os.listdir(chapters_dir):
        m = pattern.match(f)
        if m:
            files.append((int(m.group(1)), os.path.join(chapters_dir, f)))
    return [p for _, p in sorted(files)]


def chapter_path(project_root, chapter_num):
    """获取指定章节的规范路径。"""
    chapters_dir = os.path.join(project_root, "chapters")
    return os.path.join(chapters_dir, f"chapter_{int(chapter_num):04d}.md")


def report_path(project_root, chapter_num, report_type="quality"):
    """获取审核报告的规范路径。"""
    reports_dir = os.path.join(project_root, "reports")
    return os.path.join(reports_dir, f"chapter_{int(chapter_num):04d}_{report_type}.md")


def humanized_path(project_root, chapter_num):
    """获取去 AI 味后章节的规范路径。"""
    chapters_dir = os.path.join(project_root, "chapters")
    return os.path.join(chapters_dir, f"chapter_{int(chapter_num):04d}_humanized.md")
