#!/usr/bin/env python3
"""
detect_patterns.py — AI 腔模式扫描器

基于 shared/references/ai_patterns.md 的 51 条模式进行快速正则扫描。
输出 JSON 格式的匹配报告，供 ai-humanizer 使用。

用法:
  python detect_patterns.py --file <章节文件>
  python detect_patterns.py --file <章节文件> --severity 4  # 仅报告严重度 >= 4
"""
import argparse
import json
import re
import sys


# 51 条 AI 腔模式（简化正则版，详细定义见 ai_patterns.md）
PATTERNS = [
    # A. 内容模式
    ("A1.过度拔高", r'具有(?:重要|深远|极其)意义|(?:标志着|谱写了|开创了).{0,20}(?:新阶段|新局面|新篇章)|为.{0,10}注入.{0,10}活力', 4),
    ("A2.空洞关注", r'值得一提的是|值得关注的是|不可否认|不容忽视|毋庸置疑|众所周知', 3),
    ("A3.时代开场", r'随着.{0,20}的(?:不断)?发展|在当今.{0,20}的大背景下|在.{0,20}的浪潮中', 3),
    ("A4.尾巴拔高", r'体现了.{0,20}的深刻|彰显了.{0,20}的价值|折射出.{0,20}的逻辑|蕴含着.{0,20}的启示', 4),
    ("A5.模糊权威", r'专家表示|业内人士认为|有关研究显示|据悉|相关报告指出|不少学者指出', 2),
    ("A6.挑战展望", r'尽管.{0,30}但是.{0,30}(?:挑战|未来|展望)', 3),

    # B. 过度解释
    ("B1.复述解释", r'也就是说|换句话说|简单来说|换言之|总而言之|总之', 3),
    ("B2.不是而是", r'不是.{0,20}，而是', 2),
    ("B4.因果过密", r'因为.{0,20}所以.{0,20}因此.{0,20}从而|因为.{0,10}因此.{0,10}进而', 2),
    ("B5.定义开头", r'所谓.{0,10}(?:是指|指的是|的定义是)', 2),

    # C. 情感模式
    ("C1.心中涌起", r'心中涌起|一阵.{0,5}涌上心头|心底泛起|心中.{0,2}(?:一|充满了)', 4),
    ("C2.不由得", r'不由得|忍不住.{0,2}地|不禁.{0,2}地|下意识地', 3),
    ("C3.叹气苦笑", r'叹了口气|苦笑(?:一声|道|着)|摇了摇头', 4),
    ("C4.感到一阵", r'感到一阵|只感到|顿感|忽感', 3),
    ("C5\\d.目光眼神", r'目光.{0,3}(?:闪烁|一凝|复杂)|眼神.{0,3}(?:一凝|一冷)|眼中.{0,3}闪过|眸光', 3),
    ("C6.嘴角泛滥", r'嘴角.{0,3}(?:扬起|勾起|一抽|抽搐|浮现)', 3),

    # D. 动作模式
    ("D1.开始进行", r'开始.{0,5}(?:起来|进行)|进行.{0,10}的|做出.{0,5}的动作', 2),
    ("D2.缓缓慢慢", r'缓缓(?!升起|落下|睁开|闭上)|慢慢(?!的|地)|渐渐(?!的|地)|徐徐|逐步', 2),
    ("D4.武器模板", r'寒光一闪|化为一道.{0,5}(?:流光|光芒|虹)|光芒大盛|恐怖的(?:气息|威压)', 4),
    ("D5.修炼流水", r'盘膝(?:坐|而).{0,20}运转.{0,20}(?:涌入|灌入)', 4),

    # E. 冗余修饰
    ("E1.非常极其", r'(?:非常|极其|无比|十分)(?!重要|危险|强大)', 2),
    ("E2.某种程度", r'一定程度[上内]|某种程度上|某种意义上', 2),
    ("E4.似乎仿佛", r'似乎.{0,5}(?:是|有|在|不)|仿佛.{0,5}(?:是|有|在|看)', 2),

    # F. 结构模式
    ("F1.总结腔", r'总的来说|综上所述|总的来看|总的来讲|总而言之', 4),
    ("F3.排比收尾", r'(?:让我们|使我们|让我们共同).{0,30}让我们', 5),
    ("F4.Emoji列点", r'[✅❌💡🔥🚀⭐✨💪🎯⚠️📌🔴🟢🟡]', 4),
    ("F5.加粗标记", r'\*\*[^*]{2,30}\*\*', 3),

    # G. 对话模式
    ("G1.说道重复", r'(.{2,8}(?:说道|问道|答道|喊道|怒道|冷道|笑道|淡道))', 3),
    ("G2.副词语气", r'(?:淡淡|冷冷|沉沉|苦笑|轻轻|微微)(?:道|地说|地说|一笑)', 3),

    # H. 叙事模式
    ("H1.他不知道", r'他不知道的是|殊不知', 5),
    ("H2.命运齿轮", r'命运的齿轮', 5),
    ("H3.暗流涌动", r'暗流涌动|暴风雨前的宁静', 4),
    ("H5.章节结尾", r'(?:这场|真正的|一切).{0,10}(?:才刚刚开始|还在后面|才刚刚拉开)', 5),

    # I. 节奏模式
    ("I4.一就", r'一.{1,3}就.{1,3}(?:一.{1,3}就)', 2),
]


def scan(text):
    """扫描文本，返回所有匹配。"""
    hits = []
    for name, pattern, severity in PATTERNS:
        for m in re.finditer(pattern, text):
            start = max(0, m.start() - 15)
            end = min(len(text), m.end() + 15)
            context = text[start:end].replace('\n', ' ')
            hits.append({
                "pattern": name,
                "severity": severity,
                "position": m.start(),
                "match": m.group()[:40],
                "context": f"...{context}...",
            })
    hits.sort(key=lambda h: (-h["severity"], h["position"]))
    return hits


def summary(hits):
    """生成摘要统计。"""
    sev_counts = {}
    cat_counts = {}
    for h in hits:
        s = h["severity"]
        sev_counts[s] = sev_counts.get(s, 0) + 1
        cat = h["pattern"][0]  # A-I
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    return {
        "total": len(hits),
        "by_severity": sev_counts,
        "by_category": cat_counts,
        "severity_5_count": sev_counts.get(5, 0),
        "severity_4_count": sev_counts.get(4, 0),
        "pass_clean": len(hits) == 0,
        "pass_acceptable": sev_counts.get(5, 0) == 0 and sev_counts.get(4, 0) <= 3,
    }


def print_report(hits, min_severity=1):
    """打印可读报告。"""
    hits = [h for h in hits if h["severity"] >= min_severity]
    s = summary(hits)

    print(f"\n{'='*50}")
    print(f"  AI 腔模式扫描报告")
    print(f"{'='*50}")
    print(f"  总匹配数: {s['total']}")
    print(f"  严重度分布: {s['by_severity']}")
    print(f"  类别分布: {s['by_category']}")
    print(f"  可发布: {'是' if s['pass_clean'] else '否'}")
    print(f"  可接受: {'是' if s['pass_acceptable'] else '否 (需修改)'}")

    if s["severity_5_count"] > 0:
        print(f"\n  --- 严重度5 (必须修改) ---")
        for h in hits:
            if h["severity"] == 5:
                print(f"  [{h['pattern']}] {h['context'][:100]}")

    if s["severity_4_count"] > 0:
        print(f"\n  --- 严重度4 (建议修改) ---")
        for h in hits:
            if h["severity"] == 4:
                print(f"  [{h['pattern']}] {h['context'][:100]}")

    return s


def main():
    parser = argparse.ArgumentParser(description="AI 腔模式扫描器")
    parser.add_argument("--file", required=True, help="章节文件路径")
    parser.add_argument("--severity", type=int, default=1, help="最低报告严重度(1-5)")
    parser.add_argument("--json", action="store_true", help="输出JSON格式")
    args = parser.parse_args()

    with open(args.file, 'r', encoding='utf-8') as f:
        text = f.read()

    hits = scan(text)

    if args.json:
        output = {
            "file": args.file,
            "summary": summary(hits),
            "hits": [h for h in hits if h["severity"] >= args.severity],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print_report(hits, min_severity=args.severity)

    # Exit code
    s = summary(hits)
    if s["severity_5_count"] > 0:
        sys.exit(1)
    elif s["severity_4_count"] > 3:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
