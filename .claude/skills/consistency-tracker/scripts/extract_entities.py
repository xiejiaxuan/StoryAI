#!/usr/bin/env python3
"""
extract_entities.py — 从章节文本中提取实体信息

提取：角色名出现、地点引用、物品/功法引用、世界规则触发、情节线推进
输出 JSON，供 consistency-tracker 合并到 entity_db.json

用法:
  python extract_entities.py --file <章节文件> --chapter 5
  python extract_entities.py --file <章节文件> --chapter 5 --entity-db entity_db.json
"""
import argparse
import json
import os
import re
import sys


def extract_characters(text, known_names=None):
    """从文本中提取角色名出现记录。"""
    if known_names is None:
        known_names = []
    mentions = {}
    # 中文名格式：2-4字，前面有特定上下文
    patterns = [
        r'(?:^|\n|。|！|？|，|、|""|'')([^\x00-\xff]{2,4})(?:道|说|想|看|走|来|去|站|坐|笑|叹|问|答|喊|叫|怒|冷|淡|轻)',
        r'(?:林阎|柳如烟|苏铭|云澈|秦峰|沈清|顾北辰|叶尘|萧炎|林动|牧尘|叶凡|石昊|韩立|方平|许七安)',
    ]
    for pat in patterns:
        for m in re.finditer(pat, text):
            name = m.group(1) if m.lastindex and m.lastindex >= 1 else m.group(0)
            name = name.strip()
            if len(name) >= 2:
                mentions[name] = mentions.get(name, 0) + 1
    # 只保留出现 > 1 次的
    return {k: v for k, v in mentions.items() if v > 1}


def extract_locations(text, known_locations=None):
    """提取地点引用。"""
    if known_locations is None:
        known_locations = []
    # 常见地点后缀
    location_suffix = r'(?:镇|城|国|界|域|宗|派|门|殿|阁|塔|院|山|谷|林|海|河|湖|渊|原|府|都|市|村|庄|岛|峰|崖|洞)'
    pattern = rf'[一-鿿]{{1,3}}{location_suffix}'
    locations = {}
    for m in re.finditer(pattern, text):
        loc = m.group()
        locations[loc] = locations.get(loc, 0) + 1
    return {k: v for k, v in locations.items() if v > 1}


def extract_artifacts(text):
    """提取物品/功法/法宝引用。"""
    artifact_patterns = [
        r'[一-鿿]{2,4}(?:剑|刀|枪|棍|斧|鞭|弓|戟|锤|鼎|炉|塔|镜|珠|印|符|幡|环|索|针|扇|琴|笔|卷|图|石|玉|丹|药)',
        r'(?:功法|仙术|神通|秘术|禁术|法术|武技|剑法|刀法|拳法|掌法|身法|心法)[：:]*[一-鿿]{1,6}',
    ]
    artifacts = {}
    for pat in artifact_patterns:
        for m in re.finditer(pat, text):
            art = m.group()
            artifacts[art] = artifacts.get(art, 0) + 1
    return artifacts


def extract_rule_triggers(text):
    """检测世界规则触发点——角色使用了哪些力量体系的能力。"""
    triggers = []
    rule_patterns = [
        (r'(?:突破|晋升|晋级).{0,10}(?:境界|修为|等级)', '境界突破'),
        (r'(?:运转|催动|施展|使用|释放).{0,10}(?:灵力|真气|魔力|元力|法力|斗气)', '力量使用'),
        (r'(?:神识|神念|神魂).{0,10}(?:探查|扫过|覆盖|锁定)', '神识运用'),
        (r'(?:空间|时间|因果|命运|生死|轮回).{0,5}(?:之力|法则|规则)', '法则触及'),
    ]
    for pat, rule_type in rule_patterns:
        count = len(re.findall(pat, text))
        if count > 0:
            triggers.append({"type": rule_type, "count": count})
    return triggers


def extract_plot_threads(text, chapter_num):
    """检测情节线推进——新信息、伏笔、未解决事件。"""
    threads = []
    # 新信息引入
    reveals = re.findall(r'(?:发现|得知|明白|原来|竟然|居然|终于)(.{5,30})', text)
    for r in reveals[:5]:
        threads.append({"type": "reveal", "content": r.strip(), "chapter": chapter_num})
    # 未解决事件（悬念/危机）
    cliffhangers = re.findall(r'(?:突然|忽然|就在这时|冷不|猛地|蓦地)(.{5,40})', text)
    for c in cliffhangers[:3]:
        threads.append({"type": "cliffhanger", "content": c.strip(), "chapter": chapter_num})
    return threads


def main():
    parser = argparse.ArgumentParser(description="从章节提取实体")
    parser.add_argument("--file", required=True, help="章节文件路径")
    parser.add_argument("--chapter", type=int, required=True, help="章号")
    parser.add_argument("--entity-db", help="已有实体数据库路径")
    args = parser.parse_args()

    with open(args.file, 'r', encoding='utf-8') as f:
        text = f.read()

    # 加载已知实体
    known_chars = []
    known_locs = []
    if args.entity_db and os.path.exists(args.entity_db):
        with open(args.entity_db, 'r', encoding='utf-8') as f:
            db = json.load(f)
        known_chars = list(db.get("characters", {}).keys())
        known_locs = list(db.get("locations", {}).keys())

    result = {
        "chapter": args.chapter,
        "characters": extract_characters(text, known_chars),
        "locations": extract_locations(text, known_locs),
        "artifacts": extract_artifacts(text),
        "rule_triggers": extract_rule_triggers(text),
        "plot_threads": extract_plot_threads(text, args.chapter),
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    main()
