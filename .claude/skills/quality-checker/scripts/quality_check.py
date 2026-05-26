#!/usr/bin/env python3
"""
quality_check.py — 小说章节 33 维度质量审核

用法:
  python quality_check.py --file <章节文件> --quick       # 5项核心检查
  python quality_check.py --file <章节文件> --full         # 全量33维检查
  python quality_check.py --file <章节文件> --full --prev <前章文件>  # 含跨章检查
  python quality_check.py --dir <目录> --full              # 批量检查
"""
import argparse
import json
import os
import re
import sys
from collections import Counter

# ============================================================
# 检测词库
# ============================================================

AI_MARKERS = [
    "暗思涌起", "心理描写", "环境描写", "动作描写", "神态描写",
    "命运的齿轮", "未完待续", "故事才刚开始", "真正的危机",
    "风暴即将来临", "他不知道的是", "殊不知",
    "一场更大的", "更大的风暴", "而这，仅仅只是",
    "这才是开始", "真正的考验", "悄然拉开帷幕",
    "命运的齿轮开始了转动", "命运的齿轮已然转动",
    "看似平静的", "平静之下暗藏", "暗流涌动", "暴风雨前的宁静",
    "一场腥风血雨", "心中暗想", "暗自思忖",
    "心中涌起", "涌上心头", "内心充满了",
    "嘴角扬起", "嘴角勾起", "嘴角一抽", "嘴角抽搐",
    "目光闪烁", "目光一凝", "目光复杂", "眼神一凝", "眼中闪过",
    "不由得", "忍不住", "不禁", "下意识地",
    "叹了口气", "苦笑一声", "摇了摇头",
    "具有重要意义", "值得关注的是", "不可否认", "不容忽视",
    "随着……的发展", "在当今……的大背景下",
    "总的来说", "综上所述", "总而言之",
    "拉开了帷幕",
]

TEMPLATE_ENDINGS = [
    "命运的齿轮", "未完待续", "真正的危机", "风暴即将来临",
    "拉开帷幕", "才刚刚开始", "而这只是", "这只是",
    "更大的阴谋", "更大的棋局", "更大的风暴",
    "真正的考验", "真正的挑战", "真正的冒险",
    "故事才刚刚开始", "一切都才刚刚开始",
    "暗思涌起", "暴风雨前的宁静", "暗流涌动",
    "腥风血雨", "殊不知", "他不知道的是",
    "一场更大的", "悄然拉开帷幕",
]

PROTAGONIST_KEYWORDS = ["主角", "林阎", "叶尘", "苏铭", "云澈", "秦峰", "沈清", "顾北辰"]

SETTING_KEYWORDS = [
    "云雾", "山", "林", "河", "天", "地", "空", "夜", "风", "月", "星",
    "光", "影", "雾", "雪", "雨", "雷", "电", "城", "殿", "楼", "阁",
    "塔", "院", "门", "窗", "街", "巷", "路"
]

EMOTION_KEYWORDS = [
    "愤怒", "惊讶", "喜悦", "悲伤", "恐惧", "犹豫", "坚定", "兴奋",
    "无奈", "欣慰", "苦涩", "甜蜜", "温暖", "激动", "平静", "紧张", "放松"
]

ACTION_KEYWORDS = [
    "冲", "挥", "打", "走", "跑", "跳", "躲", "闪", "劈", "斩", "刺",
    "抓", "拿", "举", "握", "推", "拉", "翻", "跃", "飞", "掠", "退", "进"
]

CONFLICT_KEYWORDS = [
    "战", "斗", "敌", "杀", "恨", "怒", "惊", "险", "危", "难",
    "痛", "死", "伤", "败", "胜", "攻", "守", "防", "挡", "避",
    "逃", "追", "围", "困", "破", "灭"
]

PROGRESSION_KEYWORDS = [
    "发现", "得知", "明白", "决定", "出发", "遇见", "出现", "传来", "收到", "遇到",
    "突破", "晋级", "领悟", "觉醒", "获得", "开启"
]

SCENE_TRANSITION_KEYWORDS = [
    "此时", "这时", "随后", "接着", "与此同时", "片刻后",
    "第二天", "次日", "转眼", "忽然", "蓦地", "冷不", "就在这时"
]


# ============================================================
# 工具函数
# ============================================================

def count_chinese(text):
    return sum(1 for c in text if '一' <= c <= '鿿')


# ============================================================
# 第一层：基础指标（5 项）
# ============================================================

def c1_word_count(text):
    cn = count_chinese(text)
    return ("字数达标(≥8000)", f"{cn}字", cn >= 8000)


def c2_chinese_purity(text):
    cn = count_chinese(text)
    stripped = re.sub(r'\s', '', text)
    total = len(stripped)
    pct = cn / total * 100 if total > 0 else 0
    return ("中文纯度(≥95%)", f"{pct:.1f}%", pct >= 95)


def c3_ai_markers(text):
    found = [m for m in AI_MARKERS if m in text]
    return ("AI标记词(0个)", f"{len(found)}个 {str(found)[:80]}", len(found) == 0)


def c4_template_ending(text):
    last500 = text[-500:]
    found = [e for e in TEMPLATE_ENDINGS if e in last500]
    return ("模板化结尾(无)", f"{len(found)}个", len(found) == 0)


def c5_paragraph_length(text):
    paragraphs = [p for p in text.split('\n\n') if p.strip()]
    if not paragraphs:
        return ("段落长度", "无段落", True)
    lengths = [len(p) for p in paragraphs]
    mx = max(lengths)
    avg = sum(lengths) // len(lengths)
    return ("段落长度合理", f"最长{mx}字 平均{avg}字", mx < 3000)


# ============================================================
# 第二层：文风与结构（8 项）
# ============================================================

def c6_repetition_rate(text):
    sents = re.split(r'[，。！？；\n]+', text)
    sents = [s.strip() for s in sents if 10 <= len(s) <= 30]
    if len(sents) < 5:
        return ("重复率(<10%)", "句子太少", True)
    counter = Counter(sents)
    dup = sum(v - 1 for v in counter.values() if v > 1)
    rate = dup / len(sents) * 100
    return ("重复率(<10%)", f"{rate:.1f}%", rate < 10)


def c7_dialogue_ratio(text):
    dialogue = sum(len(d) for d in re.findall(r'[""](.*?)[""]', text))
    dialogue += sum(len(d) for d in re.findall(r"[''](.*?)['']", text))
    total = count_chinese(text)
    ratio = dialogue / total * 100 if total > 0 else 0
    return ("对话比例(25-55%)", f"{ratio:.0f}%", 25 <= ratio <= 55)


def c8_punctuation_density(text):
    cn = count_chinese(text)
    punct = sum(1 for c in text if c in '，。！？、；：""''（）【】《》『』')
    ratio = punct / cn * 100 if cn > 0 else 0
    return ("标点密度合理", f"每百字{ratio:.0f}个", 25 <= ratio <= 65)


def c9_paragraph_variance(text):
    paragraphs = [p for p in text.split('\n\n') if p.strip()]
    if len(paragraphs) < 3:
        return ("段落节奏变化", "N/A", True)
    lengths = [len(p) for p in paragraphs]
    avg = sum(lengths) / len(lengths)
    var = sum((l - avg) ** 2 for l in lengths) / len(lengths)
    cv = (var ** 0.5) / avg if avg > 0 else 0
    return ("段落节奏变化", f"变异系数{cv:.2f}", 0.3 <= cv <= 1.5)


def c10_sentence_length(text):
    sents = re.split(r'[，。！？；]+', text)
    sents = [s.strip() for s in sents if s.strip()]
    if not sents:
        return ("句长", "无句子", True)
    lengths = [count_chinese(s) for s in sents]
    avg = sum(lengths) / len(lengths)
    return ("句长合理", f"均{avg:.0f}字/句", 8 <= avg <= 25)


def c11_scene_transitions(text):
    markers = sum(1 for kw in SCENE_TRANSITION_KEYWORDS if kw in text)
    paras = max(len(text.split('\n\n')), 1)
    ratio = markers / paras * 100
    return ("场景转换自然", f"每段{ratio:.1f}次", 0.3 <= ratio <= 2.0)


def c12_emotion_words(text):
    count = sum(1 for kw in EMOTION_KEYWORDS if kw in text)
    cn = count_chinese(text)
    density = count / cn * 1000 if cn > 0 else 0
    return ("情感词密度", f"千字{density:.1f}", 2 <= density <= 15)


def c13_repeated_word_check(text):
    words = re.findall(r'[一-鿿]{2,4}', text)
    counter = Counter(words)
    cn = count_chinese(text)
    overuse = [w for w, c in counter.most_common(20) if c > cn / 500]
    return ("无高频重复词", f"{len(overuse)}个", len(overuse) == 0)


# ============================================================
# 第三层：内容与大纲（7 项）
# ============================================================

def c14_progression_check(text):
    has_something = any(kw in text for kw in PROGRESSION_KEYWORDS)
    return ("有情节推进", "有新事件" if has_something else "无明显推进", has_something)


def c15_protagonist_presence(text):
    found = []
    for kw in PROTAGONIST_KEYWORDS:
        c = text.count(kw)
        if c > 0:
            found.append(f"{kw}x{c}")
    if not found:
        return ("主角出现密度", "未检测到已知主角名", False)
    total_mentions = sum(text.count(kw) for kw in PROTAGONIST_KEYWORDS)
    cn = count_chinese(text)
    density = total_mentions / cn * 1000 if cn > 0 else 0
    return ("主角出现密度", f"千字{density:.1f}次", 0.5 <= density <= 15)


def c16_action_density(text):
    actions = sum(1 for kw in ACTION_KEYWORDS for _ in re.finditer(kw, text))
    cn = count_chinese(text)
    density = actions / cn * 1000 if cn > 0 else 0
    return ("动作词密度", f"千字{density:.0f}", 2 <= density <= 10)


def c17_internal_monologue(text):
    internal = sum(text.count(w) for w in ["想", "暗道", "自语", "心想", "心道"])
    cn = count_chinese(text)
    density = internal / cn * 1000 if cn > 0 else 0
    return ("内心独白适度", f"千字{density:.1f}", 1 <= density <= 8)


def c18_setting_description(text):
    setting = sum(1 for kw in SETTING_KEYWORDS for _ in re.finditer(kw, text))
    cn = count_chinese(text)
    density = setting / cn * 1000 if cn > 0 else 0
    return ("场景描写适当", f"千字{density:.0f}", 3 <= density <= 20)


def c19_conflict_tension(text):
    conflict = sum(1 for kw in CONFLICT_KEYWORDS for _ in re.finditer(kw, text))
    cn = count_chinese(text)
    density = conflict / cn * 1000 if cn > 0 else 0
    return ("有冲突张力", f"千字{density:.0f}", 5 <= density <= 25)


def c20_core_setting_check(text):
    golden = len(re.findall(
        r'(?:铜钱|太初|道|功法|灵力|灵气|修为|实力|修炼|突破|境界|力量|能力|神秘|系统)',
        text
    ))
    cn = count_chinese(text)
    density = golden / cn * 1000 if cn > 0 else 0
    return ("核心设定提及", f"千字{density:.0f}", density > 1)


# ============================================================
# 第四层：格式与规范（5 项）
# ============================================================

def c21_numeric_format(text):
    arabic = len(re.findall(r'(?<!第)[0-9]+(?!章)', text))
    return ("无阿拉伯数字", f"{arabic}处", arabic == 0)


def c22_english_words(text):
    english = re.findall(r'[a-zA-Z]{2,}', text)
    english = [w for w in english if w.lower() not in ('md', 'txt', 'py', 'api')]
    return ("无英文单词", f"{len(english)}个", len(english) == 0)


def c23_format_consistency(text):
    lines = text.split('\n')
    short = [l for l in lines if 0 < len(l.strip()) < 5 and l.strip() not in ('', '一', '二', '三')]
    return ("格式一致", f"{len(short)}异常短行", len(short) < 10)


def c24_special_chars(text):
    weird = re.findall(r'[^一-鿿　-〿＀-￯\n\r\t\s'
                       r'，。！？、；：""''（）【】《》『』…——～·a-zA-Z0-9]', text)
    return ("无特殊字符", f"{len(weird)}个", len(weird) < 5)


def c25_chapter_word_count(text):
    cn = count_chinese(text)
    return ("字数在合理范围", f"{cn}字 (8000-20000)", 8000 <= cn <= 20000)


# ============================================================
# 第五层：高级分析（8 项）
# ============================================================

def c26_opening_hook(text):
    opening = text[:300]
    hooks = re.findall(r'(?:突然|忽然|猛地|一声|轰|砰|嗖|竟|却发现|只见|只听|就在这时|冷不)', opening)
    return ("开头有吸引力", f"{len(hooks)}个勾子词", len(hooks) >= 1)


def c27_ending_quality(text):
    ending = text[-300:]
    paragraphs = ending.split('\n\n')
    last_para = paragraphs[-1] if paragraphs else ""
    too_short = len(last_para) < 100
    return ("结尾完整", f"末段{len(last_para)}字", not too_short)


def c28_pacing_variety(text):
    paragraphs = [p for p in text.split('\n\n') if p.strip()]
    if len(paragraphs) < 4:
        return ("段落长短交替", "N/A", True)
    pairs = [abs(len(paragraphs[i]) - len(paragraphs[i + 1]))
             for i in range(len(paragraphs) - 1)]
    avg_diff = sum(pairs) / len(pairs) if pairs else 0
    return ("段落长短交替", f"相邻差异均值{avg_diff:.0f}字", avg_diff > 50)


def c29_character_consistency(text):
    char_names = re.findall(r'(?:林阎|柳如烟|张三|李四|王五|赵六)', text)
    if not char_names:
        return ("角色一致性", "N/A", True)
    return ("角色名称一致", f"{len(set(char_names))}个角色", True)


def c30_vocabulary_richness(text):
    chars = re.findall(r'[一-鿿]', text)
    if not chars:
        return ("词汇丰富度", "N/A", True)
    richness = len(set(chars)) / len(chars)
    return ("词汇丰富度", f"{richness:.3f}", richness > 0.1)


def c31_person_check(text):
    first_person = len(re.findall(r'(?:我(?!们)|我的|我自)', text))
    third_person = len(re.findall(r'(?:他|她|其)', text))
    total = first_person + third_person
    if total == 0:
        return ("人称一致", "N/A", True)
    ratio = first_person / total * 100
    return ("第三人称一致", f"第一人称{ratio:.0f}%", ratio < 5)


def c32_scene_completeness(text):
    dialogue = len(re.findall(r'[""].*?[""]', text))
    action = len(re.findall(r'(?:冲|挥|打|走|跑|跳|躲|闪|劈|斩|刺|抓|拿|举|握|推|拉)', text))
    has_scene = bool(re.search(r'(?:云雾|山|林|天|地|夜|风|月|星)', text[:500]))
    complete = dialogue > 0 and action > 0 and has_scene
    return ("场景完整(对话+动作+环境)", f"对话{dialogue}/动作{action}/场景{'有' if has_scene else '无'}", complete)


def c33_cross_chapter_continuity(text, prev_text=""):
    if not prev_text:
        return ("跨章衔接", "N/A", True)
    words_cur = set(re.findall(r'[一-鿿]{4,}', text))
    words_prev = set(re.findall(r'[一-鿿]{4,}', prev_text))
    overlap = len(words_cur & words_prev)
    return ("跨章无大段重复", f"{overlap}个4字词组重复", overlap < 20)


# ============================================================
# 检查索引
# ============================================================

QUICK_CHECKS = [c1_word_count, c2_chinese_purity, c3_ai_markers, c4_template_ending, c5_paragraph_length]

FULL_CHECKS = [
    c1_word_count, c2_chinese_purity, c3_ai_markers, c4_template_ending, c5_paragraph_length,
    c6_repetition_rate, c7_dialogue_ratio, c8_punctuation_density, c9_paragraph_variance,
    c10_sentence_length, c11_scene_transitions, c12_emotion_words, c13_repeated_word_check,
    c14_progression_check, c15_protagonist_presence, c16_action_density, c17_internal_monologue,
    c18_setting_description, c19_conflict_tension, c20_core_setting_check,
    c21_numeric_format, c22_english_words, c23_format_consistency, c24_special_chars,
    c25_chapter_word_count,
    c26_opening_hook, c27_ending_quality, c28_pacing_variety, c29_character_consistency,
    c30_vocabulary_richness, c31_person_check, c32_scene_completeness, c33_cross_chapter_continuity,
]

LAYER_NAMES = [
    "第一层：基础指标",
    "第二层：文风与结构",
    "第三层：内容与大纲",
    "第四层：格式与规范",
    "第五层：高级分析",
]
LAYER_SIZES = [5, 8, 7, 5, 8]


# ============================================================
# 输出
# ============================================================

def format_report(filename, results):
    lines = []
    passed = sum(1 for _, _, p in results if p)
    total = len(results)

    lines.append(f"\n{'='*60}")
    lines.append(f"  {filename[:30]} 质量审核: {passed}/{total} 通过")
    lines.append(f"{'='*60}")

    idx = 0
    for layer_name, size in zip(LAYER_NAMES, LAYER_SIZES):
        p = sum(1 for _, _, ok in results[idx:idx+size] if ok)
        status = "OK" if p == size else "!!"
        lines.append(f"\n[{status}] {layer_name} ({p}/{size}):")
        for name, value, ok in results[idx:idx+size]:
            icon = "[PASS]" if ok else "[FAIL]"
            lines.append(f"  {icon} {name}: {value}")
        idx += size

    ratio = passed / total if total > 0 else 0
    if ratio >= 0.9:
        grade = "优秀"
    elif ratio >= 0.7:
        grade = "良好"
    else:
        grade = "需改进"
    lines.append(f"\n总评: {grade} ({passed}/{total})")
    return '\n'.join(lines)


def run_checks(text, prev_text="", full=False):
    checks = FULL_CHECKS if full else QUICK_CHECKS
    results = []
    for fn in checks:
        if fn == c33_cross_chapter_continuity:
            results.append(fn(text, prev_text))
        else:
            results.append(fn(text))
    return results


def main():
    parser = argparse.ArgumentParser(description="小说33维度质量审核")
    parser.add_argument("--file", help="章节文件路径")
    parser.add_argument("--dir", help="目录路径(批量)")
    parser.add_argument("--full", action="store_true", help="全量33维检查")
    parser.add_argument("--quick", action="store_true", help="快速检查(默认)")
    parser.add_argument("--prev", help="前章文件路径(跨章检查)")
    parser.add_argument("--json", action="store_true", help="输出JSON格式")
    args = parser.parse_args()

    files = []
    if args.file:
        files.append(args.file)
    elif args.dir:
        files = sorted([os.path.join(args.dir, f) for f in os.listdir(args.dir)
                       if f.endswith('.md') and 'chapter' in f])
    else:
        print("用法: python quality_check.py --file <文件> --full")
        sys.exit(1)

    for filepath in files:
        if not os.path.exists(filepath):
            print(f"文件不存在: {filepath}")
            continue
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()

        prev_text = ""
        if args.prev and os.path.exists(args.prev):
            with open(args.prev, 'r', encoding='utf-8') as f:
                prev_text = f.read()

        results = run_checks(text, prev_text, full=args.full)

        if args.json:
            output = [{"name": name, "value": value, "pass": ok} for name, value, ok in results]
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print(format_report(os.path.basename(filepath), results))


if __name__ == "__main__":
    main()
