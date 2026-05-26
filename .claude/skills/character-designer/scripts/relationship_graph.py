#!/usr/bin/env python3
"""relationship_graph.py — 角色关系网络验证"""

import json
import re
import sys


def extract_character_names(text):
    """从角色文档中提取所有角色名。"""
    names = set()
    # 匹配 "## 角色档案：XXX"
    for m in re.finditer(r'##\s+角色档案[：:]\s*(.+)', text):
        names.add(m.group(1).strip())
    # 匹配 "**姓名**：XXX"
    for m in re.finditer(r'\*\*姓名\*\*[：:]\s*(.+)', text):
        names.add(m.group(1).strip())
    return names


def extract_relationships(text):
    """从角色文档中提取所有关系声明。返回 [(角色1, 角色2, 关系类型), ...]"""
    relationships = []
    # 匹配 "**关系**：XXX - YYY"
    rel_section = re.search(r'##\s+关系网络\n(.*?)(?=\n##|\Z)', text, re.DOTALL)
    if not rel_section:
        return relationships
    lines = rel_section.group(1).strip().split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('- ') or line.startswith('* '):
            relationships.append(line.lstrip('- *').strip())
    return relationships


def check_orphans(names, relationships_text):
    """检查是否有角色没有关系连接。"""
    connected = set()
    for rel in relationships_text:
        for name in names:
            if name in rel:
                connected.add(name)
    return names - connected


def check_power_balance(characters_data):
    """检查势力分布是否合理。返回警告。"""
    warnings = []
    factions = {}
    for name, data in characters_data.items():
        faction = data.get("faction", "未知")
        if faction not in factions:
            factions[faction] = []
        factions[faction].append(name)

    # 如果一个势力角色数超过 60%，警告
    total = sum(len(v) for v in factions.values())
    for faction, members in factions.items():
        if total > 0 and len(members) / total > 0.6:
            warnings.append(f"势力 '{faction}' 拥有 {len(members)}/{total} 角色，占比过高")
    return warnings


def main():
    if len(sys.argv) < 2:
        print("用法: python relationship_graph.py <characters.md>")
        sys.exit(1)

    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        text = f.read()

    names = extract_character_names(text)
    relationships = extract_relationships(text)

    print(f"\n{'='*50}")
    print(f"  角色关系网络验证")
    print(f"{'='*50}")
    print(f"\n  角色数: {len(names)}")
    print(f"  关系声明数: {len(relationships)}")

    orphans = check_orphans(names, relationships)
    if orphans:
        print(f"\n  孤立角色 (无关系连接):")
        for name in orphans:
            print(f"    - {name}")

    # 检查关系双向性
    for rel in relationships:
        print(f"    {rel}")

    expected_rels = len(names) * (len(names) - 1) // 2
    print(f"\n  理论最大关系数: {expected_rels}，实际: {len(relationships)}")

    if len(relationships) < len(names):
        print(f"  警告: 关系数少于角色数，可能存在角色之间缺乏互动设计")


if __name__ == "__main__":
    main()
