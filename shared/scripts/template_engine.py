#!/usr/bin/env python3
"""template_engine.py — 模板加载与变量注入"""

import os
import re
from pathlib import Path


def get_templates_dir():
    """查找 shared/templates/ 目录绝对路径。"""
    script_dir = Path(__file__).resolve().parent
    for p in [script_dir, *script_dir.parents]:
        tmpl = p / "shared" / "templates"
        if tmpl.is_dir():
            return str(tmpl)
    return None


def get_references_dir():
    """查找 shared/references/ 目录绝对路径。"""
    script_dir = Path(__file__).resolve().parent
    for p in [script_dir, *script_dir.parents]:
        ref = p / "shared" / "references"
        if ref.is_dir():
            return str(ref)
    return None


def load_template(template_name):
    """加载指定名称的模板文件。"""
    tmpl_dir = get_templates_dir()
    if not tmpl_dir:
        raise FileNotFoundError("无法找到 shared/templates/ 目录")
    filepath = os.path.join(tmpl_dir, template_name)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"模板文件不存在: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def load_reference(reference_name):
    """加载指定名称的参考文档。"""
    ref_dir = get_references_dir()
    if not ref_dir:
        raise FileNotFoundError("无法找到 shared/references/ 目录")
    filepath = os.path.join(ref_dir, reference_name)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"参考文档不存在: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def inject_variables(template_text, variables):
    """替换模板中的 {{变量名}} 占位符。"""
    def replacer(match):
        key = match.group(1).strip()
        return str(variables.get(key, match.group(0)))
    return re.sub(r'\{\{(\w+)\}\}', replacer, template_text)


def validate_sections(text, required_sections):
    """验证文本中是否包含所有必须的 ## 标题。返回缺失列表。"""
    headers = set()
    for m in re.finditer(r'^##\s+(.+)$', text, re.MULTILINE):
        headers.add(m.group(1).strip())
    missing = [s for s in required_sections if s not in headers]
    return missing


def list_templates():
    """列出所有可用模板。"""
    tmpl_dir = get_templates_dir()
    if not tmpl_dir:
        return []
    return sorted([f for f in os.listdir(tmpl_dir) if f.endswith('.md')])


def list_references():
    """列出所有可用参考文档。"""
    ref_dir = get_references_dir()
    if not ref_dir:
        return []
    return sorted([f for f in os.listdir(ref_dir) if f.endswith('.md')])
