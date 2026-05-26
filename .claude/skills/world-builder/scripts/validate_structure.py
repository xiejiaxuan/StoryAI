#!/usr/bin/env python3
"""validate_structure.py — 验证世界观文档的完整性"""

import re
import sys


REQUIRED_SECTIONS = [
    "世界观概述",
    "时代与时间线",
    "地理与地点",
    "力量体系",
    "势力与组织",
    "历史事件表",
    "文化与社会",
    "世界规则",
    "核心冲突",
]


def validate(text):
    """检查文档是否包含所有必要章节。返回 (是否通过, 缺失列表, 警告列表)。"""
    headers = []
    for m in re.finditer(r'^##\s+(.+)$', text, re.MULTILINE):
        headers.append(m.group(1).strip())

    missing = [s for s in REQUIRED_SECTIONS if not any(s in h for h in headers)]
    warnings = []

    # 检查每个 section 是否有内容
    sections = re.split(r'^##\s+', text, flags=re.MULTILINE)[1:]
    for sec in sections:
        lines = sec.strip().split('\n')
        header = lines[0].strip()
        content = '\n'.join(lines[1:]).strip()
        if len(content) < 50:
            warnings.append(f"'{header}' 内容过短（{len(content)} 字），建议补充")
        if '<!--' in content and '-->' in content and content.count('<!--') > 2:
            warnings.append(f"'{header}' 仍保留大量模板注释，请替换为实际内容")

    passed = len(missing) == 0
    return passed, missing, warnings


def main():
    if len(sys.argv) < 2:
        print("用法: python validate_structure.py <world_settings.md>")
        sys.exit(1)

    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        text = f.read()

    passed, missing, warnings = validate(text)

    print(f"\n{'='*50}")
    print(f"  世界观文档结构验证: {'通过' if passed else '不通过'}")
    print(f"{'='*50}")

    if missing:
        print(f"\n缺失章节 ({len(missing)}):")
        for s in missing:
            print(f"  - {s}")

    if warnings:
        print(f"\n警告 ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")

    if passed and not warnings:
        print("\n  所有检查通过。")


if __name__ == "__main__":
    main()
