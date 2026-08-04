"""
StoryMap 构建脚本
==================
读取 story_data.json → 嵌入到 index.html → 输出自包含 HTML

使用: python build.py
"""
import json, os, re

DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(DIR, "story_data.json")
HTML_PATH = os.path.join(DIR, "index.html")

# 读取 JSON 数据
with open(JSON_PATH, encoding="utf-8") as f:
    data = json.load(f)

# 读取 HTML 模板
with open(HTML_PATH, encoding="utf-8") as f:
    html = f.read()

# 替换嵌入数据（匹配 EMBEDDED_DATA = {...};）
json_str = json.dumps(data, ensure_ascii=False)
new_embed = f"const EMBEDDED_DATA = {json_str};"

# 检查是否已有嵌入数据
if "const EMBEDDED_DATA =" in html:
    html = re.sub(r'const EMBEDDED_DATA = .*?;', new_embed, html, count=1)
else:
    # 首次嵌入：在 loadData 函数前插入
    html = html.replace("function loadData()", f"{new_embed}\n\nfunction loadData()")

# 确保 loadData 直接使用嵌入数据（不使用 fetch）
html = html.replace(
    "async function loadData() {",
    "function loadData() {"
)

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✓ 构建完成: {len(html):,} bytes")
print(f"  位置: {HTML_PATH}")
print(f"  数据: {len(data['locations'])} 地点 | {len(data['characters'])} 角色 | {len(data.get('items',[]))} 物品 | {len(data.get('relations',[]))} 关系")
print(f"  浏览器直接打开即可使用，无需服务器")
