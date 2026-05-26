#!/usr/bin/env python3
"""
ai_detector_quick.py — AI 标记词快速检测（Top-20 高频模式）

用法:
  python ai_detector_quick.py --file <章节文件>
  返回: 标记数量、位置列表、严重度分级
"""
import argparse
import re
import sys


# Top-20 最常见的 AI 标记模式
QUICK_PATTERNS = [
    # (正则, 名称, 严重度)
    (r'命运的齿轮', '命运齿轮', 5),
    (r'暗思涌起', '暗思涌起', 5),
    (r'真正的危机才刚刚开始', '危机才刚开始', 5),
    (r'更大的风暴即将来临', '更大的风暴', 5),
    (r'真正的考验[，。]', '真正的考验', 5),
    (r'殊不知', '殊不知', 5),
    (r'他不知道的是', '他不知道的是', 5),
    (r'心中涌起', '心中涌起', 4),
    (r'一阵.{0,5}涌上心头', '涌上心头', 4),
    (r'心中.{0,5}充满了', '心中充满', 4),
    (r'内心充满了', '内心充满', 4),
    (r'暗流涌动', '暗流涌动', 4),
    (r'暴风雨前的宁静', '暴风雨前宁静', 4),
    (r'未完待续', '未完待续', 4),
    (r'才刚刚开始', '才刚刚开始', 3),
    (r'拉开了帷幕', '拉开帷幕', 3),
    (r'悄然.{0,3}拉开', '悄然拉开', 3),
    (r'一场更大的', '一场更大的', 3),
    (r'嘴角.{0,5}(?:扬起|勾起|一抽|抽搐)', '嘴角动作', 3),
    (r'目光.{0,5}(?:闪烁|一凝|复杂|闪过)', '目光描写', 3),
]


def scan(text):
    """扫描文本，返回匹配列表。"""
    hits = []
    for pattern, name, severity in QUICK_PATTERNS:
        for m in re.finditer(pattern, text):
            # 获取上下文
            start = max(0, m.start() - 20)
            end = min(len(text), m.end() + 20)
            context = text[start:end].replace('\n', ' ')
            hits.append({
                "pattern": name,
                "severity": severity,
                "position": m.start(),
                "match": m.group(),
                "context": f"...{context}...",
            })
    hits.sort(key=lambda h: (-h["severity"], h["position"]))
    return hits


def main():
    parser = argparse.ArgumentParser(description="AI 标记快速检测")
    parser.add_argument("--file", required=True, help="章节文件路径")
    parser.add_argument("--threshold", type=int, default=3, help="最低报告严重度 (1-5)")
    parser.add_argument("--max-hits", type=int, default=50, help="最多输出匹配数")
    args = parser.parse_args()

    with open(args.file, 'r', encoding='utf-8') as f:
        text = f.read()

    hits = scan(text)
    hits = [h for h in hits if h["severity"] >= args.threshold]

    sev5 = sum(1 for h in hits if h["severity"] == 5)
    sev4 = sum(1 for h in hits if h["severity"] == 4)
    sev3 = sum(1 for h in hits if h["severity"] == 3)

    print(f"\n{'='*50}")
    print(f"  AI 标记快速检测: {args.file}")
    print(f"{'='*50}")
    print(f"  严重度 5: {sev5} 处")
    print(f"  严重度 4: {sev4} 处")
    print(f"  严重度 3: {sev3} 处")
    print(f"  总计: {len(hits)} 处\n")

    if sev5 > 0:
        print("  严重 (必须修改):")
        for h in hits[:args.max_hits]:
            if h["severity"] == 5:
                print(f"    [{h['pattern']}] {h['context'][:80]}")
    if sev4 > 0:
        print("\n  警告 (建议修改):")
        for h in hits[:args.max_hits]:
            if h["severity"] == 4:
                print(f"    [{h['pattern']}] {h['context'][:80]}")

    # 返回 exit code: 0=干净, 1=有严重问题, 2=仅有警告
    if sev5 > 0:
        sys.exit(1)
    elif sev4 > 3:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
