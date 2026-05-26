#!/usr/bin/env python3
"""text_utils.py — 中文文本处理工具"""

import re
from collections import Counter


def count_chinese(text):
    """统计中文字符数（仅 CJK 统一表意文字）。"""
    return sum(1 for c in text if '一' <= c <= '鿿')


def count_punctuation(text):
    """统计中文标点符号数。"""
    punct_set = set('，。！？、；：""''（）【】《》『』…——～·')
    return sum(1 for c in text if c in punct_set)


def count_total_chars(text):
    """总字符数（含标点、英文、数字）。"""
    return len(text)


def estimate_reading_time(text, cpm=400):
    """估算阅读时间（分钟），默认每分钟 400 字。"""
    cn = count_chinese(text)
    return cn / cpm if cpm > 0 else 0


def extract_dialogue(text):
    """提取所有对话行，返回 [(说话内容, 位置), ...]"""
    patterns = [
        r'[""]([^""]+)[""]',
        r"['']([^'']+)['']",
    ]
    results = []
    for pat in patterns:
        for m in re.finditer(pat, text):
            results.append((m.group(1), m.start()))
    return results


def dialogue_ratio(text):
    """对话文本占比（基于中文引号内容）。"""
    dl = sum(len(d) for d, _ in extract_dialogue(text))
    cn = count_chinese(text)
    return dl / cn * 100 if cn > 0 else 0


def split_sentences(text):
    """按句末标点分句。"""
    return [s.strip() for s in re.split(r'[。！？；\n]+', text) if s.strip()]


def split_paragraphs(text):
    """按空行分段。"""
    return [p.strip() for p in text.split('\n\n') if p.strip()]


def sentence_length_stats(text):
    """句长统计：均值、标准差、最小、最大。"""
    sents = split_sentences(text)
    if not sents:
        return {"avg": 0, "std": 0, "min": 0, "max": 0, "count": 0}
    lengths = [count_chinese(s) for s in sents]
    avg = sum(lengths) / len(lengths)
    var = sum((l - avg) ** 2 for l in lengths) / len(lengths)
    return {
        "avg": round(avg, 1),
        "std": round(var ** 0.5, 1),
        "min": min(lengths),
        "max": max(lengths),
        "count": len(lengths),
    }


def paragraph_length_stats(text):
    """段落长度统计：均值、标准差、变异系数。"""
    paras = split_paragraphs(text)
    if not paras:
        return {"avg": 0, "std": 0, "cv": 0, "min": 0, "max": 0, "count": 0}
    lengths = [count_chinese(p) for p in paras]
    avg = sum(lengths) / len(lengths)
    var = sum((l - avg) ** 2 for l in lengths) / len(lengths)
    std = var ** 0.5
    return {
        "avg": round(avg, 0),
        "std": round(std, 0),
        "cv": round(std / avg, 2) if avg > 0 else 0,
        "min": min(lengths),
        "max": max(lengths),
        "count": len(lengths),
    }


def word_frequency(text, word_len=2):
    """N-gram 词频统计（默认 2 字词组）。"""
    chars = re.findall(r'[一-鿿]', text)
    grams = [''.join(chars[i:i+word_len]) for i in range(len(chars) - word_len + 1)]
    return Counter(grams)


def vocabulary_richness(text):
    """词汇丰富度：不重复字数 / 总字数。"""
    chars = re.findall(r'[一-鿿]', text)
    return len(set(chars)) / len(chars) if chars else 0


def chinese_purity(text):
    """中文纯度：中文字符 / (总字符 - 空白)。"""
    stripped = re.sub(r'\s', '', text)
    cn = count_chinese(stripped)
    return cn / len(stripped) * 100 if stripped else 0


def has_arabic_digits(text):
    """检查是否含阿拉伯数字。排除章节标题如 第1章。"""
    return bool(re.search(r'(?<!第)[0-9]+(?!章)', text))


def has_english_words(text, min_len=2):
    """检查是否含英文单词（>= min_len 字母）。"""
    return bool(re.search(rf'[a-zA-Z]{{{min_len},}}', text))
